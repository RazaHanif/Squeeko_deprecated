# This is where the main python API will live
# Will support endpoints for the Whisper Model & Pyannote

# Please go watch the 20min youtube fast api intro - link in notes.md
# FastAPI == newer Django? == node.py

from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from models import AudioRequest, SummaryRequest
from tasks import transcribe, diarize, summarize
from utils.auth import verify_token

app = FastAPI()

# Middleware or dependency to protect routes
async def require_auth(request: Request):
    token = request.headers.get("Authorization")
    if not token or not await verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.post("/transcribe")
async def transcribe_audio(data: AudioRequest, auth: bool = Depends(require_auth)):
    result = await transcribe.run(data.audio_url)
    return {"transcript": result}

@app.post("/diarize")
async def diarize_audio(data: AudioRequest, auth: bool = Depends(require_auth)):
    result = await diarize.run(data.audio_url)
    return {"speaker_segments": result}

@app.post("/summarize")
async def summarize_audio(data: AudioRequest, auth: bool = Depends(require_auth)):
    result = await summarize.run(data.audio_url)
    return {"summary": result}

@app.get("/")
def root():
    return {"message": "Server is live!"}