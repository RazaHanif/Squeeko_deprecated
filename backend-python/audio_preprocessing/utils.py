from pydub import AudioSegment
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

# Returns duration of audio file in seconds
def get_duration(file_path: str) -> float:
    # First check if file is supported
    file_type = is_supported(file_path)
        
    if file_type:
        try:
            audio = AUDIO_LOADERS[file_type](file_path)
            return audio.duration_seconds
        except Exception as e:
            print(f"Error loading or processing '{file_path}': {e}")
            return 0.0
    else:
        print(f"Unsupported Audio format: {file_path}")
        return 0.0    

# Checks if audio file is in a supported format
def is_supported(file_path: str) -> str | None:
    _, extension = os.path.splitext(file_path) 
    file_type = extension.lstrip('.').lower()
    
    # Check if file is supported
    if file_type in SUPPORTED_FORMATS:
        return file_type
    else:
        return None