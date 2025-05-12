import pytest
import httpx
import os
import tempfile
from pathlib import Path

from main import app
from utils.auth import TEST_TOKEN


# Rename these later
TEST_AUDIO_DIR = Path(__file__).parent / "audio"

TEST_SILENCE_MP3 = TEST_AUDIO_DIR / "silence.mp3"
TEST_SHORT_ENG_MP3 = TEST_AUDIO_DIR / "test_en.mp3"
TEST_SHORT_FA_MP3 = TEST_AUDIO_DIR / "test_fa.mp3"
TEST_AUDIO_DIR.mkdir(exist_ok=True)

if not TEST_SILENCE_MP3.exists():
    # Create a dummy silence file (requires pydub and its dependencies like ffmpeg)
    # Alternatively, include a small pre-made silence file in your test repo
    try:
        from pydub import AudioSegment
        silence = AudioSegment.silent(duration=1000) # 1 second silence
        silence.export(TEST_SILENCE_MP3, format="mp3")
        print(f"Created dummy silence file: {TEST_SILENCE_MP3}")
    except ImportError:
        print("WARNING: pydub not installed. Cannot create dummy audio files. Tests requiring uploads may fail.")
    except Exception as e:
         print(f"WARNING: Failed to create dummy silence file {TEST_SILENCE_MP3}: {e}. Tests requiring uploads may fail.")


# --- Fixture for Async Test Client
@pytest.fixture(scope="module")
async def async_client():
    """ Provides an async httpx client for testing FastAPI app """
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

        
# --- Helper to open audio files in binary
def open_audio_file(file_path: Path):
    """ Opens an audio file in binary read """
    return file_path.open("rb")


# --- Helper to create dummy merged sugments for /summarize test
def create_dummy_merged_segments():
    """ Creates a simple list of dummy merged segments for testing summarization """
    return [
        {"speaker": "Speaker A", "start": 0.0, "end": 5.5, "text": "Hello this is a test transcript segment."},
        {"speaker": "Speaker A", "start": 6.0, "end": 10.2, "text": "And this is a response from another speaker."},
        {"speaker": "Speaker A", "start": 11.0, "end": 15.0, "text": "Let's talk about action items."},
        {"speaker": "Speaker A", "start": 16.0, "end": 20.0, "text": "Okay, I will complete task X by Friday."}
    ]
    

# --- TEST FUNCTIONS ---

# Test the root endpoint
@pytest.mark.asyncio
async def test_read_main(async_client: httpx.AsyncClient):
    """ Tests the basic root endpoint """
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == { "message": "Squeeko backend is live!" }
    

# Test the /transcribe endpoint (transcription only)
@pytest.mark.asyncio
async def test_transcribe_audio(async_client: httpx.AsyncClient):
    """Tests the /transcribe endpoint with a dummy audio file."""
  
    if not TEST_SILENCE_MP3.exists():
         pytest.skip("Dummy audio file not found for transcription test.")

    with open_audio_file(TEST_SILENCE_MP3) as f:
        files = {"audio_file": (TEST_SILENCE_MP3.name, f, "audio/mp3")}

        response = await async_client.post(
            "/transcribe",
            files=files,
            headers={"Authorization": TEST_TOKEN}
        )

    assert response.status_code == 200
    response_json = response.json()
    assert "transcript" in response_json
    assert isinstance(response_json["transcript"], str)

    # expand later to use a file with known speech, assert specific content here
    # assert "expected phrase" in response_json["transcript"].lower()


# Test the /transcribe_and_diarize endpoint
@pytest.mark.asyncio
async def test_transcribe_and_diarize_audio(async_client: httpx.AsyncClient):
    """Tests the /transcribe_and_diarize endpoint with a dummy audio file."""

    # Ideally, use a short audio file with 2 distinct speakers for this test
    # For simplicity, using silence file as a basic structure check example
    if not TEST_SILENCE_MP3.exists():
         pytest.skip("Dummy audio file not found for transcribe+diarize test.")

    with open_audio_file(TEST_SILENCE_MP3) as f:
        files = {"audio_file": (TEST_SILENCE_MP3.name, f, "audio/mp3")}

        response = await async_client.post(
            "/transcribe_and_diarize",
            files=files,
            headers={"Authorization": TEST_TOKEN}
        )

    assert response.status_code == 200
    response_json = response.json()
    assert "segments" in response_json
    assert isinstance(response_json["segments"], list)

    # If using audio with expected speech/speakers, check list is not empty and segment structure
    # if response_json["segments"]:
    #    first_segment = response_json["segments"][0]
    #    assert "speaker" in first_segment
    #    assert "start" in first_segment
    #    assert "end" in first_segment
    #    assert "text" in first_segment


# Test the /summarize endpoint
@pytest.mark.asyncio
async def test_summarize_audio(async_client: httpx.AsyncClient):
    """Tests the /summarize endpoint with dummy merged segments."""

    dummy_segments = create_dummy_merged_segments()

    response = await async_client.post(
        "/summarize",
        json={"segments": dummy_segments},
        headers={"Authorization": TEST_TOKEN}
    )

    assert response.status_code == 200
    response_json = response.json()
    assert "summary" in response_json
    summary_data = response_json["summary"]

    # Check the structure of the returned summary (should be the dict from summarize.run)
    assert isinstance(summary_data, dict)
    assert "main_topic" in summary_data
    assert "summary" in summary_data
    assert "key_points" in summary_data
    assert "tasks_to_complete" in summary_data
    assert isinstance(summary_data["main_topic"], str)
    assert isinstance(summary_data["summary"], str)
    assert isinstance(summary_data["key_points"], list)
    assert isinstance(summary_data["tasks_to_complete"], list)
    # You could add assertions here to check if the summary content seems reasonable
    # based on your dummy segments, but this is harder with LLM outputs.
    # e.g., assert "task X" in str(summary_data["tasks_to_complete"]) # Check if task X was identified


# Test authentication failure
@pytest.mark.asyncio
async def test_auth_failure(async_client: httpx.AsyncClient):
    """Tests that endpoints return 401 without correct authorization."""

    # Try accessing a protected endpoint without any header
    response_no_header = await async_client.post("/transcribe", files={})
    assert response_no_header.status_code == 401

    # Try accessing with a wrong token
    response_wrong_token = await async_client.post(
        "/transcribe",
        files={},
        headers={"Authorization": "Bearer wrong_token"}
    )
    assert response_wrong_token.status_code == 401

    # Add checks for other protected endpoints like /transcribe_and_diarize and /summarize
    response_td_no_header = await async_client.post("/transcribe_and_diarize", files={})
    assert response_td_no_header.status_code == 401

    response_sum_no_header = await async_client.post("/summarize", json={})
    assert response_sum_no_header.status_code == 401