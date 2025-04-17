from dotenv import load_dotenv
import os
import whisper
import time

load_dotenv()
whisper_model = os.getenv("WHISPER_MODEL", "tiny")

enAudio = "./audio/test_en.mp3"
faAudio = "./audio/test_fa.mp3"

start = time.time()

# Declare device cpu & fp16 false - cuz intel sucks - this will change for prod 
""" 
for production the values change to: load_model(") & transcribe(audioPath)
"""
model = whisper.load_model("medium", device="cpu")
result = model.transcribe(faAudio, language="fa", fp16=False, task="translate")

end = time.time()

print(f"\nTranscription took {end - start:2f} seconds")
print(result["text"])
