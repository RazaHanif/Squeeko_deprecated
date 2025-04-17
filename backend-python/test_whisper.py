import whisper

model = whisper.load_model("base")
result = model.transcribe("./audio/test.mp3")

print(result["text"])

