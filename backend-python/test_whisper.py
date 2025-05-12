import os
import whisper
import time

whisper_model = "base"

enAudio = "./tests/audio/test_en.mp3"
faAudio = "./tests/audio/test_fa.mp3"

start = time.time()
print("Starting Transcription")

# Declare device cpu & fp16 false - cuz intel sucks - this will change for prod 
# for production the values change to: load_model(") & transcribe(audioPath)

print("Loading model")
model = whisper.load_model(whisper_model, device="cpu")
print("Model Loaded")

print("starting english test")
enResult = model.transcribe(enAudio, fp16=False, task="translate")
print("completed english test...starting farsi test")
faResult = model.transcribe(faAudio, fp16=False, task="translate")
print("completed farsi test")

end = time.time()

print(f"English Test File: {enResult['text']}")
print(f"Persian Test File: {faResult['text']}")
