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

def load_pyannote_pipeline(from_local_cache_only: bool = False):
    """
    Loads the Pyannote diarization pipeline into memory. Intended to be called once at startup.
    Requires HUGGING_FACE_HUB_TOKEN env var unless loading strictly from cache.

    Args:
        from_local_cache_only (bool): If True, strictly load from the local cache without checking the Hugging Face Hub online. Requires the model to be downloaded previously.
    """
    
    global pyannote_pipeline_instance
    if pyannote_pipeline_instance is None: 
        try:
            pyannote_pipeline_instance = Pipeline.from_pretrained(
                PYANNOTE_PIPELINE_NAME,
                use_auth_token=HUGGING_FACE_HUB_TOKEN,
                device=DEVICE,
                local_files_only=from_local_cache_only
            )
            
            if from_local_cache_only:
                print("Note: Pyannote loaded strictly from local cache")
                
        except Exception as e:
            print(f"Fatel Error: Failed to load Pyannote pipeline '{PYANNOTE_PIPELINE_NAME}': {e}")
            pyannote_pipeline_instance = None
            # In prod raise a specific exception to stop startup
            
async def run(audio_file_path: str) -> list[dict] | None:
    """
    Runs speaker diarization on an audio file using the loaded Pyannote pipeline.
    Runs the blocking pipeline call in a thread pool.

    Args:
        audio_file_path (str): The path to the temporary audio file on the server.

    Returns:
        list[dict]: A list of dictionaries, where each dict represents a speaker segment
                    with 'speaker', 'start', and 'end' keys (in seconds).
                    Returns None on failure or if pipeline is not loaded.
    """
    global pyannote_pipeline_instance
    if pyannote_pipeline_instance is None:
        print("Pyannote pipeline not loaded")
        return None
    
    