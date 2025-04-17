from dotenv import load_dotenv
import os
import whisper

load_dotenv()
whisper_model = os.getenv("WHISPER_MODEL", "tiny")

# Declare device cpu & fp16 false - cuz intel sucks - this will change for prod 
""" 
for production the values change to: load_model(") & transcribe(audioPath)
"""
model = whisper.load_model(whisper_model, device="cpu")
result = model.transcribe("./audio/test.mp3", fp16=False)

print(result["text"])

