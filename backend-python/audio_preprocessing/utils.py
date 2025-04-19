import os 

SUPPORTED_FORMATS = ["mp3", "wav", "m4a", "acc", "ogg", "flac", "webm"]

# Checks if audio file is in a supported format
def is_supported(file_path: str) -> bool:
    _, extension = os.path.splitext(file_path) 
    file_type = extension.lstrip('.').lower()
    
    # Check if file is supported
    if file_type in SUPPORTED_FORMATS:
        return True
    else:
        return False