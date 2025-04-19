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

