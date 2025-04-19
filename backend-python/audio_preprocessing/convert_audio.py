import os
import pydub
import subprocess
import tempfile


# Converts w.e file type to the correct WAV format

def to_wav(input_path: str) -> AudioSegment | None:
    # Create a temp file with a .wav extension to store the FFmpeg output
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        output_path = tmp_file.name


    # FFmpeg command to convert the input to most optimized file type for Whisper
    # Format: WAV | Codec: PCM 16-Bit | Sample Rate: 16kHz | Channel: Mono | 
    command = [
        "ffmpeg", 
        "-i", input_path, 
        "-acodec", "pcm_s16le", 
        "-ac", "1", 
        "-ar", "16000", 
        output_path
    ]
    
    try:
        # Execute the FFmpeg Command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Load & return the converted WAV file into a pydub AudioSegment Object
        return pydub.AudioSegment.from_wav(output_path)
    
    # Error Handling
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg conversion:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return Code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"An error occurred after FFmpeg conversion: {e}")
        return None
    
    finally:
        # Clean up the temporary WAV file
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
            