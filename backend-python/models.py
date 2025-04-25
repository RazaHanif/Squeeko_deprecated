from pydantic import BaseModel
from typing import List, Dict, Any # Import types for the merged_segments structure
# If using Pydantic v2, you might import from typing_extensions

class AudioRequest(BaseModel):
    """
    Request model for endpoints that take an audio URL or path.
    NOTE: Not used for file uploads via UploadFile = File(...).
    """
    audio_url: str # Assuming this is a URL or path accessible by the server

# Update SummaryRequest to accept the merged_segments structure
class SummaryRequest(BaseModel):
    """
    Request model for the summarization endpoint.
    Assumes the client sends the merged transcription/diarization segments.
    """
    # Define a field to hold the list of merged segments
    segments: List[Dict[str, Any]]

    # Optional: You might include other fields if needed, e.g., user_id, preferences
    # user_id: str
    # format_preference: str = "structured" # e.g., "structured", "paragraph"