import os 


# Returns duraction of audio file in seconds
def get_audio_duration(file_path: str) -> float:
    # TODO: use pydub to calculate duration
    file_type = is_supported(file_path)
        
    if file_type is not None:
        return 
    else:
        return 0

# Checks if audio file is in a supported format
def is_supported(file_path: str) -> bool:
    supported_formats = ["mp3", "wav", "m4a", "acc", "ogg", "flac", "webm", "mp4"]

    # Get file type
    _, extension = os.path.splitext(file_path) 
    file_type = extension.lstrip('.').lower()
    
    # Check if file is supported
    if file_type in supported_formats:
        return file_type
    else:
        return None