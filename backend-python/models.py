# Define structure of audio & summary

from pydantic import BaseModel

class AudioRequest(BaseModel):
    user_id: str
    audio_url: str

class SummaryRequest(BaseModel):
    user_id: str
    audio_url: str