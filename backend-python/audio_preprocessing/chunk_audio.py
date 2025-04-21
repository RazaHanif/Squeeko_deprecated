from pydub import AudioSegment
import os

def split(audio_segment: AudioSegment, chunk_length_ms: int = os.getenv("CHUNK_MS")) -> list[AudioSegment]:
    """
    Splits an AudioSegment into chunks of a specified length.

    Args:
        audio_segment (AudioSegment): The input audio segment object (expected to be
                                      trimmed and downscaled).
        chunk_length_ms (int): The target length of each chunk in milliseconds.
                               Defaults to 30000 ms (30 seconds), which is optimal
                               for Whisper processing.

    Returns:
        list[AudioSegment]: A list of AudioSegment objects, each representing a chunk.
                            The last chunk may be shorter than chunk_length_ms.
                            Returns an empty list if the input segment is empty.
    """
    
    if len(audio_segment) == 0:
        return []
    
    chunks = []
    audio_length = len(audio_segment)
    current_start_ms = 0 
    
    # Iterate through the audio, taking slices of chunk_length_ms
    while current_start_ms < audio_length:
        # Calculate the end point for the current chunk - Ensure the end point does not exceed the total audio length
        current_end_ms = min(current_start_ms + chunk_length_ms, audio_length)
        
        # Extract chunk using slice
        chunk = audio_segment[current_start_ms:current_end_ms]
        
        # Add to chunk list
        chunks.append(chunk)
        
        # Update pointer
        current_start_ms += chunk_length_ms
        
    return chunks