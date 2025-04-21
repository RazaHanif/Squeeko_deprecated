from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi import UplaodFile, File

import tempfile
import os
import shutil
from tasks import transcribe, diarize, summarize

# Idk if i need these models?
import models
import utils.auth


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
    diarize.load_pyannote_pipeline(from_local_cache_only=False)
    
     # Optional: Check if both models loaded successfully and raise error if critical
    if transcribe.whisper_model_instance is None:
        print("Startup Error: Whisper model failed to load. Transcription will not work.")
        # raise RuntimeError("Whisper model load failed")
    if diarize.pyannote_pipeline_instance is None:
        print("Startup Error: Pyannote pipeline failed to load. Diarization will not work.")
        # raise RuntimeError("Pyannote pipeline load failed")
    
    print("Model is loaded")
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

# --- Helper
def merge_transcription_and_diarization(
    transcription_results: list[dict], # List of chunk results from transcribe.run_transcription_pipeline
    diarization_segments: list[dict], # List of speaker segments from diarize.run
    original_audio_length_ms: int # Needed to calculate absolute chunk times
) -> list[dict]:
    """
    Merges transcription results (with segment timestamps relative to chunks)
    with speaker diarization segments (with absolute timestamps).

    Args:
        transcription_results (list[dict]): Results from transcribe.run_transcription_pipeline.
        diarization_segments (list[dict]): Results from diarize.run.
        original_audio_length_ms (int): The length of the original audio in milliseconds.

    Returns:
        list[dict]: A list of merged segments, each including speaker, absolute start/end times, and text.
                    Includes error markers for failed chunks.
    """
    merged_segments = []
    diarization_index = 0
    
    # Assume fixed chunk length (maybe gloablize with CHUNK_LENGTH)
    chunk_length_ms = 30000
    
    for chunk_index, chunk_result in enumerate(transcription_results):
        if isinstance(chunk_result, dict) and "segments" in chunk_result:
            # Calc absolute start time of the current chunk in seconds
            chunk_start_time_abs_sec = chunk_index * (chunk_length_ms / 1000.00)
            
            for segment in chunk_result["segments"]:
                segment_start_abs_sec = chunk_start_time_abs_sec + segment.get("start", 0)
                segment_end_abs_sec = chunk_start_time_abs_sec + segment.get("end", 0)
                
                # Find corresonding speaker for this segment
                current_speaker = "Unknown"
                
                # Advance the diarization_index to efficiently find potentially overlapping segments
                while diarization_index < len(diarization_segments) -1 and diarization_segments[diarization_index + 1].get("start", float('inf')) <= segment_start_abs_sec:
                    diarization_index += 1
                    
                # Now, check the current diarization segment (at diarization_index) for overlap
                if diarization_index < len(diarization_segments):
                    dia_seg = diarization_segments[diarization_index]
                    dia_start = dia_seg.get("start", float('-inf'))
                    dia_end = dia_seg.get("end", float('inf'))
                    
                    if max(segment_start_abs_sec, dia_start) < min(segment_end_abs_sec, dia_end):
                        current_speaker = dia_seg.get("speaker", "Unknown")
                        
                merged_segments.append({
                    "speaker": current_speaker,
                    "start": round(segment_start_abs_sec, 3),
                    "end": round(segment_end_abs_sec, 3),
                    "text": segment.get("text", "")
                })
        elif isinstance(chunk_result, dict) and "error" in chunk_result:
            error_start_abs_sec = chunk_index
    

# --- Routes

@app.get("/")
def root():
    """ 
    Basic root endpoint to check if the server is live
    """
    return {"message": "Squeeko backend is live!"}

@app.post("/transcribe")
async def transcribe_audio(
    audio_file: UplaodFile = File(...),
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
            


@app.post("/diarize")
async def diarize_audio(data: models.AudioRequest, auth: bool = Depends(require_auth)):
    try:
        result = await diarize.run(data.audio_url)
        return {"speaker_segments": result}
    except Exception as e:
        print(f"An error occurred during diarization: {e}")
        raise HTTPException(status_code=500, detail="Diarization failed.")

@app.post("/summarize")
async def summarize_audio(data: models.AudioRequest, auth: bool = Depends(require_auth)):
    try:
        result = await summarize.run(data.audio_url)
        return {"summary": result}
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed.")