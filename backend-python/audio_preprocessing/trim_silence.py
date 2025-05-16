from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import io


def apply(
    audio_segment: AudioSegment,
    silence_threshold: int = -40,
    silence_min_len_edge: int = 100,
    trim_internal: bool = True,
    silence_min_len_internal: int = 500,
    keep_silence_between: int = 500
) -> AudioSegment:
    """
    Trims leading, trailing, and optionally long pauses within an AudioSegment.

    Args:
        audio_segment (AudioSegment): The input audio segment object.
        silence_threshold (int): The energy level (in dBFS) below which audio is considered silence.
                                 Defaults to -40 dBFS. Lower values are more sensitive to quiet sounds.
        silence_min_len_edge (int): Minimum duration (in ms) for leading/trailing silence to be trimmed.
                                 Defaults to 100 ms.
        trim_internal (bool): If True, also trims/adjusts long pauses within the audio.
                              Defaults to True.
        silence_min_len_internal (int): Minimum duration (in ms) of an internal silence interval
                                      to be considered a 'long pause' for trimming/adjustment.
                                      Used only if trim_internal is True. Defaults to 500 ms.
        keep_silence_between (int): The duration (in ms) of silence to preserve between segments
                                  when trimming internal pauses. Pauses longer than
                                  silence_min_len_internal will be replaced by a pause of this length.
                                  Used only if trim_internal is True. Set to 0 to remove detected
                                  internal pauses entirely. Defaults to 500 ms.

    Returns:
        AudioSegment: The trimmed audio segment object.
    """
    print(f"Original audio length: {len(audio_segment)} ms") # ONLY FOR TESTING
    
    original_frame_rate = audio_segment.frame_rate
    
    # Trim leading & Trailing silence
    start_trim_ms = detect_leading_silence(
        audio_segment, 
        silence_thresh=silence_threshold,
        chunk_size=10,
        min_silence_len=silence_min_len_edge
    )
    end_trim_ms = detect_leading_silence(
        audio_segment.reverse(), 
        silence_thresh=silence_threshold,
        chunk_size=10,
        min_silence_len=silence_min_len_edge
    )
    
    # Apply trim by slicing AudioSegment
    
    start_index = min(start_trim_ms, len(audio_segment))
    end_index = max(0, len(audio_segment) - min(end_trim_ms, len(audio_segment)))

    trimmed_audio = audio_segment[start_index:end_index]
    print(f"Trimmed audio length: {len(trimmed_audio)} ms") # ONLY FOR TESTING
    
    # Handle Edge Case: if audio becomes empty
    if len(trimmed_audio) == 0:
        return AudioSegment.empty()
    
    # Trim long pauses in the audio (OPTIONAL)
    """ 
    if trim_internal:
        
        # split_on_silence splits the audio into chunjs based on silence longer than min_silence_len_internal
        non_silent_chunks = split_on_silence(
            trimmed_audio,
            min_silence_len=silence_min_len_internal,
            silence_thresh=silence_threshold,
            keep_silence=0
        )
        
        #  Handle Edge Case: split_on_silence might return empty list if entire segment is silent
        if not non_silent_chunks:
            return trimmed_audio
        
        # Rejoin chunks with a fixed amount of silence in between, except for the last chunk
        processed_audio = AudioSegment.empty()
        silence_segment_to_add = AudioSegment.silent(duration=keep_silence_between, frame_rate=original_frame_rate)
        
        for i, chunk in enumerate(non_silent_chunks):
            processed_audio += chunk
            if i < len(non_silent_chunks) - 1:
                processed_audio += silence_segment_to_add
                
        print(f"Internally Trimmed audio length: {len(processed_audio)} ms") # ONLY FOR TESTING
        return processed_audio
    else:
        return trimmed_audio 
    """
    
    return trimmed_audio