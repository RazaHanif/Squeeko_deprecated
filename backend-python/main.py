from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi import UploadFile, File

import tempfile
import os
from tasks import transcribe, diarize, summarize

# Idk if i need these models?
import models
import utils.auth

from pydub import AudioSegment

# --- Lifespan event for applicaiton startup/shutdown
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ 
    Loads the Whisper and Pyannote model when the application starts
    """
    print("Starting up application")
    print("Loading up Whisper model")
    transcribe.load_whisper_model()
    print("Loading up Pyannote model")
    diarize.load_pyannote_pipeline(from_local_cache_only=False)
    print("Loading up Summarization model")
    summarize.load_llm_model()
        
     # Optional: Check if models loaded successfully and raise error if critical
    if transcribe.whisper_model_instance is None:
        print("Startup Error: Whisper model failed to load. Transcription will not work.")
        # raise RuntimeError("Whisper model load failed")
    if diarize.pyannote_pipeline_instance is None:
        print("Startup Error: Pyannote pipeline failed to load. Diarization will not work.")
        # raise RuntimeError("Pyannote pipeline load failed")
    if summarize.llm_model_instance is None:
        print("Startup Error: Summarization pipeline failed to load. Summarization will not work.")
        # raise RuntimeError("Summarization pipeline load failed")
    
    print("Application startup is complete!")
    yield
    
    print("Shutting down application")
    
# --- Initalize FastAPI with the lifespan

app = FastAPI(lifespan=lifespan)


# --- Auth Dependancy
async def require_auth(request: Request):
    """ 
    FastAPI Dependency to require auth
    Checks for a valid token in the Auth header
    """
    
    token = request.headers.get("Authorization")
    if not token or not await utils.auth.verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# --- Helper function
def merge_transcription_and_diarization(
    transcription_results: list[dict],
    diarization_segments: list[dict],
    original_audio_length_ms: int
) -> list[dict]:
    """
    Merges transcription results (with segment timestamps relative to chunks)
    with speaker diarization segments (with absolute timestamps).

    Args:
        transcription_results (list[dict]): Results from transcribe.run_transcription_pipeline.
                                           Expected format is a list where each item is
                                           either a Whisper chunk result dict (with 'segments' key)
                                           or an error dict (with 'error' key).
        diarization_segments (list[dict]): Results from diarize.run.
                                           Expected format is a list of dicts with 'speaker', 'start', 'end' (seconds).
        original_audio_length_ms (int): The length of the original audio in milliseconds.

    Returns:
        list[dict]: A list of merged segments, each including speaker, absolute start/end times, and text.
                    Includes error markers for failed chunks. Returns an empty list
                    if transcription_results is empty or merging fails.
    """
 
    # print("Starting merging transcription and diarization results...")
    merged_segments = []
    diarization_index = 0 
    
    # Get Chunk time from env
    chunk_length_ms = 30000

    if not transcription_results:
        # Returning empty list means no merged segments.
        return []


    for chunk_index, chunk_result in enumerate(transcription_results):
        
        # Process successful transcription chunk results
        if isinstance(chunk_result, dict) and "segments" in chunk_result and isinstance(chunk_result["segments"], list):

            chunk_start_time_abs_sec = chunk_index * (chunk_length_ms / 1000.0)

            # Iterate through transcription segments within this chunk
            for segment in chunk_result.get("segments", []):
                if not isinstance(segment, dict) or "start" not in segment or "end" not in segment or "text" not in segment:
                    # Skip to next segment
                    continue 

                # Calculate the absolute start and end times for the transcription segment
                segment_start_abs_sec = chunk_start_time_abs_sec + segment.get("start", 0.0)
                segment_end_abs_sec = chunk_start_time_abs_sec + segment.get("end", 0.0)

                # --- Find the corresponding speaker for this transcription segment ---
                current_speaker = "Unknown"

                # Advance the diarization_index to efficiently find potentially overlapping segments
                # We look ahead as long as the *next* diarization segment starts *before or exactly at*
                # the *start* of our current transcription segment.
                while diarization_index < len(diarization_segments) - 1 and \
                      diarization_segments[diarization_index + 1].get("start", float('inf')) <= segment_start_abs_sec:
                    diarization_index += 1

                # Now, check the current diarization segment (at diarization_index) for overlap
                if diarization_index < len(diarization_segments):
                    dia_seg = diarization_segments[diarization_index]
                    dia_start = dia_seg.get("start", float('-inf'))
                    dia_end = dia_seg.get("end", float('inf'))

                    # Check if transcription segment overlaps with or is contained within the current diarization segment
                    # A simple overlap check: max(seg_start, dia_start) < min(seg_end, dia_end)
                    if max(segment_start_abs_sec, dia_start) < min(segment_end_abs_sec, dia_end):
                         current_speaker = dia_seg.get("speaker", "Unknown")


                # --- Add the merged segment to the results
                merged_segments.append({
                    "speaker": current_speaker,
                    "start": round(segment_start_abs_sec, 3),
                    "end": round(segment_end_abs_sec, 3),
                    "text": segment.get("text", "")
                })

        elif isinstance(chunk_result, dict) and "error" in chunk_result:

             # Handle error dictionaries returned by run_transcription_pipeline
             print(f"Merging: Found error result for chunk {chunk_index}: {chunk_result.get('error', 'Unknown error')}")
             error_start_abs_sec = chunk_index * (chunk_length_ms / 1000.0)
             error_end_abs_sec = min(error_start_abs_sec + (chunk_length_ms / 1000.0), original_audio_length_ms / 1000.0)

             merged_segments.append({
                 "speaker": "Error",
                 "start": round(error_start_abs_sec, 3),
                 "end": round(error_end_abs_sec, 3),
                 "text": chunk_result.get("error", "Transcription Error"),
                 "error": chunk_result.get("error", "Transcription Error") 
             })
        else:

            # Handle any other unexpected item format in the transcription_results list
            unknown_start_abs_sec = chunk_index * (chunk_length_ms / 1000.0)
            unknown_end_abs_sec = min(unknown_start_abs_sec + (chunk_length_ms / 1000.0), original_audio_length_ms / 1000.0)
            merged_segments.append({
                "speaker": "Unknown",
                "start": round(unknown_start_abs_sec, 3),
                "end": round(unknown_end_abs_sec, 3),
                "text": "[[Unexpected result format]]",
                "error": "Unexpected result format"
            })


    print(f"Merging complete. Created {len(merged_segments)} merged segments.")

    # Just to be safe, sort all segments based on start time
    merged_segments.sort(key=lambda x: x.get("start", float('inf')))

    return merged_segments

    

# --- Routes

@app.get("/")
def root():
    """ 
    Basic root endpoint to check if the server is live
    """
    return {"message": "Squeeko backend is live!"}

@app.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    auth: bool = Depends(require_auth),
    background_tasks = BackgroundTasks
):
    """ 
    Receives an audio file upload, processes it through the transcription pipleine and returns the transcription result.
    Handles temporary file storage and cleanup
    """
    
    # Check if model loaded successfully
    if transcribe.whisper_model_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Transcription service is not ready. Model failed to load on startup"
        )
        
    # Handle uploaded file: Temp storage
    # audio pipeline expects file path
    # Save the uplaoded file to a temp file server side
    temp_file_path = None
    try:
        # Create a temp file with original file extension
        file_extension = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as tmp_upload_file:
            temp_file_path = tmp_upload_file.name
            await audio_file.seek(0)
            while content :=  await audio_file.read(1024 * 1024):
                tmp_upload_file.write(content)
        
        # --- Run Pipeline
        transcription_results = await transcribe.run_transcription_pipeline(temp_file_path)
        
        
        # --- Handle Pipeline results
        if transcription_results is None:
            raise HTTPException(
                status_code=500,
                detail="Audio Processing Failed!"
            )
        
        if not transcription_results:
            # Pipeline returned empty list
            return {
                "message": "No audio contetnt detected, or processing resulted in no chunks",
                "transcript": ""
            }
            
        # --- Format final response
        combined_text = " ".join([
            r.get("text", "").strip() 
            for r in transcription_results
            if isinstance(r, dict) and "text"in r
        ])
        
        # OR return the list for more flexible client-side feautres
        # return {"chunks": transcription_results}
        
        # --- Return the successful response
        return {"transcript": combined_text}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred during transcription: {e}"
        )
    
    finally:
        # --- Clean up temp files
        # Scheduled with BackgroundTasks, ensures this happens AFTER the HTTP response has been sent
        if temp_file_path and os.path.exists(temp_file_path):
            print(f"Cleaning up temp file: {temp_file_path}")
            background_tasks.add_task(os.remove, temp_file_path)
        else:
            print("No files to cleanup")
    
# -- NEW Combined Transcribe & Diarize Endpoint
# * Might replace prevous transcribe route * 
@app.post("/transcribe_and_diarize")
async def transcribe_and_diarize_audio(
    audio_file: UploadFile = File(...),
    auth: bool = Depends(require_auth),
    background_tasks = BackgroundTasks
):
    """ 
    Receives an audio file upload, runs both transcription & diarization pipeline
    then merges the result and returns the speaker-attributed transcript segments
    
    Handles temp file storage & cleanup
    """
    
    # Check if both required models are loaded at startup
    if transcribe.whisper_model_instance is None or diarize.pyannote_pipeline_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Transcription or Diarization service not ready"
        )
        
    temp_file_path = None
    original_audio_length_ms = 0
    
    try:
        # Handle uploaded file: Temp storage
        
        file_extension = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as tmp_upload_file:
            temp_file_path = tmp_upload_file.name
            await audio_file.seek(0)
            
            while content := audio_file.read(1024 * 1024):
                tmp_upload_file.write(content)

        try:
            audio_segment_info = AudioSegment.from_file(temp_file_path)
            original_audio_length_ms = len(audio_segment_info)
        except Exception as e:
            original_audio_length_ms = 0
            
        # --- Run Diarization Pipeline
        
        # Run on full audio file
        diarization_segments = await diarize.run(temp_file_path)
        
        if diarization_segments is None:
            raise HTTPException(
                status_code=500,
                detail="Diarization Failed: No speech Detected"
            )
            
        # --- Run Transcription Pipeline
        transcription_results = await transcribe.run_transcription_pipeline(temp_file_path)
        
        if transcription_results is None:
            raise HTTPException(
                status_code=500,
                detail="Transcription Failed: Audio Processing Error"
            )
            
        # --- Merge Results
        merged_segments = merge_transcription_and_diarization(
            transcription_results,
            diarization_segments,
            original_audio_length_ms
        )
        
        return {"segments": merged_segments}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {e}"
        )
        
    finally:
        # --- Clean up temp files
        if temp_file_path and os.path.exists(temp_file_path):
            background_tasks.add_task(os.remove, temp_file_path)
        else:
            print("No files to clean")


@app.post("/summarize")
async def summarize_audio(data: models.AudioRequest, auth: bool = Depends(require_auth)):
    """ 
    Recives a summarization request, runs the summarization pipeline, and returns the summary.
    """

    try:
        result = await summarize.run(data.audio_url)
        return {"summary": result}
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed.")