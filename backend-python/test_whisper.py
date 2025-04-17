import whisper

model = whisper.load_model("tiny")
result = model.transcribe("./audio/test.mp3")

print(result["text"])

