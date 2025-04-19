import asyncio
import numpy as np
import torch
import whisper
import os
import time
from pydub import AudioSegment

# Just for testing rn?
from dotenv import load_dotenv

from audio_preprocessing import (
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
    

# Manually setting device -> CPU & FP16 -> False | Cuz intel mac sucks - will be changed in prod
# for prod the values are: load_model("medium or large") & model.transcribe(audioPath, task="translate")


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
        
        trimmed_audio = trim_silence.apply(audio_wav)
        
        if trimmed_audio is None or len(trimmed_audio) == 0:
            return []
        
        chunks = chunk_audio.split(trimmed_audio, chunk_length_ms=30000)
        
        if not chunks:
            return []
        
        return chunks
    
    except Exception as e:
        print(f"An error occurred during audio prep: {e}")
        return None
            

def run(audio_list):
    output = []
    for chunk in audio_list:
        output += transcribe_audio(chunk)
    return output

async def transcribe_audio(audio_url) ->  str:
    # Load model into cache
    model = whisper.load_model(whisper_model, device="cpu")
    
    # Run transcribtion | locking to FP32 & translating any non english to english
    result = model.transcribe(audio_url, fp16=False, task="translate")
    
    # ToDo: fix this error handling
    if not result["text"]:
        return "Error: no text was transcribed"

    # Return only the transcribed text for now...
    return result["text"]