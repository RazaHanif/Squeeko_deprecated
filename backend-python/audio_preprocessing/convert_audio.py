from pydub import AudioSegment
from utils import is_supported
import os

SUPPORTED_FORMATS = ["mp3", "wav", "m4a", "acc", "ogg", "flac", "webm"]
AUDIO_LOADERS = {
    "mp3": AudioSegment.from_mp3,
    "wav": AudioSegment.from_wav,
    "m4a": AudioSegment.from_m4a,
    "ogg": AudioSegment.from_ogg,
    "flac": AudioSegment.from_flac,
    "webm": AudioSegment.from_webm
}

# Converts input audio file to WAV for processing in whisper
# Returns new WAV file
def to_wav(input_path: str) -> AudioSegment:
    if not is_supported(input_path):
        return None
    # TODO: load audio file using pydub
    
    # TODO: export it as WAV with 16bit PCM, mono, 44100HZ?? idk what that means 
    
    
    # TODO: Save to a /temp or /processsed folder and return path
    
    pass