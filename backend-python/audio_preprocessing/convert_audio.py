from pydub import AudioSegment
import os

AUDIO_LOADERS = {
    "mp3": AudioSegment.from_mp3,
    "m4a": AudioSegment.from_m4a,
    "ogg": AudioSegment.from_ogg,
    "flac": AudioSegment.from_flac,
    "webm": AudioSegment.from_webm
}

def to_wav(input_path: str) -> AudioSegment | None:
    """ 
    Converts a supported audio file into a pydub AudioSegment object in WAV format
    
    Args:
        input_path (str): The file path for the original audio file
        
    Returns:
        AudioSegment: A pydub AudioSegment object in WAV format, or None if the conversion fails or format is not supported.
    """
    try: 
        _, extension = os.path.splitext(input_path)
        file_type = extension.lstrip('.').lower()
        
        if file_type == "wav":
            # send back 16 bit pcm just to be safe
            audio = AudioSegment.from_wav(input_path)
            return audio.set_sample_width(2)
    
        audio = AUDIO_LOADERS[file_type](input_path)
        return audio.export("temp.wav", format="wav")
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        return None