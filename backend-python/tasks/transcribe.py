# Get all the logic already created in test_whisper.py
from dotenv import load_dotenv
import os
import whisper
import time

from audio_preprocessing import (
    chunk_audio,
    convert_audio,
    downscale_audio,
    trim_silence
)

load_dotenv()
whisper_model = os.getenv("WHISPER_MODEL", "tiny")

# Audio files for testing
enAudio = "./audio/test_en.mp3"
faAudio = "./audio/test_fa.mp3"

# Manually setting device -> CPU & FP16 -> False | Cuz intel mac sucks - will be changed in prod
# for prod the values are: load_model("medium or large") & model.transcribe(audioPath, task="translate")


def prepare_audio(audio_url):
    wav_path = convert_audio.to_wav(audio_url)
    trimmed_path = trim_silence.apply(wav_path)
    downsampled_path = downscale_audio.to_16k(trimmed_path)
    chunks = chunk_audio.split(downsampled_path)
    return chunks

async def run(audio_url: str) ->  str:
    # Load model into cache
    model = whisper.load_model(whisper_model, device="cpu")
    
    # Run transcribtion | locking to FP32 & translating any non english to english
    result = model.transcribe(audio_url, fp16=False, task="translate")
    
    # ToDo: fix this error handling
    if not result["text"]:
        return "Error: no text was transcribed"

    # Return only the transcribed text for now...
    return result["text"]


