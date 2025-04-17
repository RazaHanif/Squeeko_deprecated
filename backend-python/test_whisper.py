from dotenv import load_dotenv
import os
import whisper
import time

load_dotenv()
whisper_model = os.getenv("WHISPER_MODEL", "tiny")

enAudio = "./audio/test_en.mp3"
faAudio = "./audio/test_fa.mp3"

print("Loading in Model")
start = time.time()

# Declare device cpu & fp16 false - cuz intel sucks - this will change for prod 
# for production the values change to: load_model(") & transcribe(audioPath)

model = whisper.load_model("medium", device="cpu")
print("Model Loaded")
result = model.transcribe(faAudio, fp16=False, task="translate")

end = time.time()

print(f"Transcription Completed: {end - start:2f} seconds")

print(result["text"])
