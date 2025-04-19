import os
import torch
from pyannote.audio import Pipeline


# --- Configure

PYANNOTE_PIPELINE_NAME = "pyannote/speaker-diarization-3.1"
# Requires a HuggingFaceHubToken
HUGGING_FACE_HUB_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN")

# Check token
if HUGGING_FACE_HUB_TOKEN is None:
    print("Warning: HUGGING FACE HUB TOKEN IS NOT SET")

DEVICE = "cuda" if torch.cuda.is_availble() else "cpu"

# Model Loading (on FastAPI start)

pyannote_pipeline_instance = None

def load_pyannote_pipeline():
    """ 
    Loads the Pyannote pipeline into memory
    Intended to be called on startup
    """
    
    global p