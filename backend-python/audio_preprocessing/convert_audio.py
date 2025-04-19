import os
import pydub
import subprocess
import tempfile

def to_wav(input_path: str) -> AudioSegment | None:
    """ 
    Converts a supported audio file to WAV format using FFmpeg via subproccess, then loads the resulting WAV into a pydub AudioSegment.
    
    Args:
        input_path (str): The file path for the original audio file
        
    Returns:
        AudioSegment: A pydub AudioSegment object in WAV format, or None if the conversion fails
    """
    
    # Create a temp file with a .wav extension to store the FFmpeg output
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        output_path = tmp_file.name


    # FFmpeg command to convert the input to most optimized file type for Whisper
    # Format: WAV | Codec: PCM 16-Bit | Sample Rate: 16kHz | Channel: Mono | 
    commmand = [
        "ffmpeg", 
        "-i", input_path, 
        "-acodec", "pcm_s16le", 
        "-ac", "1", 
        "-ar", "16000", 
        output_path
    ]