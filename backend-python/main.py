# This is where the main python API will live
# Will support endpoints for the Whisper Model & Pyannote

# Please go watch the 20min youtube fast api intro - link in notes.md
# FastAPI == newer Django? == node.py

from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi import UplaodFile, File

import tempfile
import os
import shutil
from tasks import transcribe, diarize, summarize

# Idk if i need these models?
import models
import utils.auth


# --- Lifespan event for applicaiton startup/shutdown
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ 
    Loads the Whisper model when the application starts
    """
    print("Starting up application")
    print("Loading up Whisper model")
    transcribe.load_whisper_model()
    print("Model is loaded")
    yield
    
    print("Shutting down application")
    
# --- Initalize FastAPI with the lifespan

app = FastAPI(lifespan=lifespan)


# --- Auth Dependancy
async def require_auth(request: Request):
    """ 
    FastAPI Dependency to require auth
    Checks for a valid token in the Auth header
    """
    
    token = request.headers.get("Authorization")
    if not token or not await utils.auth.verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# --- Routes

@app.get("/")
def root():
    """ 
    Basic root endpoint to check if the server is live
    """
    return {"message": "Squeeko backend is live!"}

@app.post("/transcribe")
async def transcribe_audio(data: models.AudioRequest, auth: bool = Depends(require_auth)):
    # Assume diari
    
    result = await transcribe.run(data.audio_url)
    return {"transcript": result}


@app.post("/diarize")
async def diarize_audio(data: models.AudioRequest, auth: bool = Depends(require_auth)):
    result = await diarize.run(data.audio_url)
    return {"speaker_segments": result}

@app.post("/summarize")
async def summarize_audio(data: models.AudioRequest, auth: bool = Depends(require_auth)):
    result = await summarize.run(data.audio_url)
    return {"summary": result}