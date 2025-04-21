import asyncio
import numpy as np
import torch
import whisper
import os
import time
from pydub import AudioSegment

# Just for testing rn?
from dotenv import load_dotenv

from ..audio_preprocessing import (
    chunk_audio,
    convert_audio,
    trim_silence
)

# Audio files for testing
enAudio = "./audio/test_en.mp3"
faAudio = "./audio/test_fa.mp3"

# --- Config ---
load_dotenv()
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny") # Use medium for prod

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

USE_FP16 = DEVICE == "cuda"

# Load model on start
whisper_model_instance = None

def load_whisper_model():
    """ Loads Whisper model into memory. Intended to be called once at startup """
    global whisper_model_instance
    if whisper_model_instance is None:
        try:
            whisper_model_instance = whisper.load_model(WHISPER_MODEL_NAME, device=DEVICE)
        except Exception as e:
            print(f"Error loading Whisper model '{WHISPER_MODEL_NAME}' on device '{DEVICE}': {e}")
            whisper_model_instance = None
            

def prepare_audio(audio_url: str) -> list[AudioSegment] | None:
    """
    Handles the full audio preprocessing pipeline: convert, trim, chunk.

    Args:
        audio_url (str): The file path or URL of the input audio file.

    Returns:
        list[AudioSegment]: A list of 30-second AudioSegment chunks,
                            or None if processing fails.
    """
    try:
        audio_wav = convert_audio.to_wav(audio_url)
        
        if audio_wav is None:
            return None
        
        # NO LONGER TRIMMING INTERNAL AUDIO
        # trimmed_audio = trim_silence.apply(audio_wav)
        
        # if trimmed_audio is None or len(trimmed_audio) == 0:
        #     return []
        
        chunks = chunk_audio.split(audio_wav)
        
        if not chunks:
            return []
        
        return chunks
    
    except Exception as e:
        print(f"An error occurred during audio prep: {e}")
        return None
            

async def transcribe_chunk_async(audio_chunk: AudioSegment, chunk_index: int) -> dict | None:
    """
    Asynchronously transcribes a single audio chunk using the loaded Whisper model.
    Runs the blocking transcribe call in a thread pool to avoid blocking the event loop.

    Args:
        audio_chunk (AudioSegment): The AudioSegment chunk to transcribe (expected mono, 16kHz, 16-bit).
        chunk_index (int): The index of the chunk (for logging/debugging).

    Returns:
        dict: The full result dictionary from model.transcribe, or None on critical error.
              Includes an 'error' key if transcription failed for this chunk.
    """
    global whisper_model_instance
    if whisper_model_instance is None:
        return {"error": f"STT Model not loaded for chunk {chunk_index}"}
    
    # Convert AudioSegment to a format Whisper can accept (Numpy Array)
    try:
        audio_data_int = np.array(audio_chunk.get_array_of_samples())
        
        if audio_chunk.sample_width == 2: # 16-bit audio
            audio_data_float32 = audio_data_int.astype(np.float32) / 32768.0
        elif audio_chunk.sample_width ==4: # 32-bit audio
            audio_data_float32 = audio_data_int.astype(np.float32) / 2147483648.0
        else: 
            audio_data_float32 = audio_data_int.astype(np.float32) / 32768.0
        
    except Exception as e:
            return {"error": f"Audio prep error for chunk {chunk_index}"}
        
        
    # Run the sync model.transcrive call in a thread pool
    # Crucial for non blocking asyncio event loop
    
    loop = asyncio.get_running_loop()
    transcription_result = None
    try:
        transcription_result = await loop.run_in_executor(
            None, # Use the default thread pool provided by asyncio
            whisper_model_instance.transcribe, # The blocking method to call
            audio_data_float32,
            task="translate",
            fp16=USE_FP16,
        )
    except Exception as e:
        transcription_result = {"text": f"[[Transcription Error for chunk {chunk_index}: {e}]]", "segments": [], "language": "error", "error": str(e)}

    return transcription_result


async def run_transcription_pipeline(audio_url: str) -> list[dict] | None:
    """
    Full asynchronous pipeline: prepare audio, transcribe chunks concurrently.

    Args:
        audio_url (str): The file path or URL of the input audio file.

    Returns:
        list[dict]: A list of transcription result dictionaries for each chunk,
                    including error information if any chunk failed.
                    Returns None if audio preparation failed entirely.
                    Returns an empty list if audio preparation resulted in no chunks.
    """
    
    # Run prepare_audio and get chunks
    audio_chunks = prepare_audio(audio_url)
    
    if audio_chunks is None:
        # Pipeline failure
        return None 
    
    if not audio_chunks:
        # No audio to transcribe
        return []
    
    # Create and run transcriptions concurrently
    
    transcription_tasks = [
        transcribe_chunk_async(chunk, i) for i, chunk in enumerate(audio_chunks)
    ]
    
    # Run tasks concurrently using asyncio.gather
    results = await asyncio.gather(*transcription_tasks, return_exceptions=True)
    
    # Return list
    return results