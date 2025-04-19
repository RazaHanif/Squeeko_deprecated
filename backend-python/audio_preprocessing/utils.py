import os 


# Returns duraction of audio file in seconds
def get_audio_duration(file_path: str) -> float:
    # TODO: use pydub to calculate duration
    pass

# Checks if audio file is in a supported format
def is_supported(file_path: str) -> bool:
    supported_formats = ["mp3", "wav", "m4a", "acc", "ogg", "flac", "webm", "mp4"]

    # Get file type
    _, extension = os.path.splitext(file_path) 
    file_type = extension.lstrip('.').lower()
    
    # Check if file is supported
    if file_type in supported_formats:
        return True
    else:
        return False