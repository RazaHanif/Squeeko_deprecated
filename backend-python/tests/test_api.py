import pytest
import pytest_asyncio
import httpx
import os
import tempfile
from pathlib import Path

from main import app

from utils.auth import TEST_TOKEN


# --- Audio paths for test files
BASE_DIR = Path(__file__).parent

enTestFile = BASE_DIR / "audio" /  "test_en.mp3"
faTestFile = BASE_DIR / "audio" / "test_fa.mp3"

# --- Expected Transcripts

EXPECTED_ENGLISH_TRANSCRIPT = """Hey, I have something to show you. I cannot be interrupted. There's a new content cop. What? A new content cop. Content cop. I haven't heard that name in almost 10 years. Well, iDubbbz did a content cop on H3. Is this like when Gen X gets excited they're doing a Goonies remake? You're excited about this? I thought iDubbbz quit YouTube. No, he just stopped saying slurs. Exactly, I thought he quit YouTube. Look, a lot has changed on YouTube since 2015. Drama videos are now usually five and a half hours long. iDubbbz is woke. So much has changed. I got married, I have seven kids now. That's a weird amount of kids in a relatively short amount of time. I switched political ideologies, gosh, probably seven times. Those kids really messed you up, huh? I was a different person back then. I'm so much better off now. I'm glad that era of YouTube is over. Do you want to watch it? Okay."""

EXPECTED_FARSI_TRANSCRIPT = """Dear friends, welcome to the Mashalv program. I took a new mic and I am very happy that I will be able to read beautiful poems for you. I am very happy to read poems from Afghanistan and Persian poetry. Thank you for your time, I love you. Have a nice day for everyone. Khuda hafiz. Keep an eye out for my content."""


# --- Fixture for the Async Test Client

# @pytest_asyncio.fixture(scope="module")
# async def async_client():
#     """Provides an asynchronous httpx client for testing the FastAPI app."""
#     transport = httpx.ASGITransport(app=app)
#     async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
#         yield client

@pytest.fixture(scope="session")



# --- Helper to open audio files in binary mode
def open_audio_file(file_path: Path):
    """Opens an audio file in binary read mode."""

    if not file_path.exists():
         raise FileNotFoundError(f"Test audio file not found: {file_path}")
    return file_path.open("rb")


# --- Helper to create dummy merged segments for /summarize test
def create_dummy_merged_segments():
    """Creates a simple list of dummy merged segments for testing summarization."""

    return [
        {"speaker": "Speaker A", "start": 0.0, "end": 5.5, "text": "Hello this is a test transcript segment."},
        {"speaker": "Speaker B", "start": 6.0, "end": 10.2, "text": "And this is a response from another speaker."},
        {"speaker": "Speaker A", "start": 11.0, "end": 15.0, "text": "Let's talk about action items."},
        {"speaker": "Speaker B", "start": 16.0, "end": 20.0, "text": "Okay, I will complete task X by Friday."}
    ]


# --- Test Functions ---

@pytest.mark.asyncio
async def test_read_main(async_client: httpx.AsyncClient):
    """Tests the basic root endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Squeeko backend is live!"}


# --- Test Transcription for English Audio ---
@pytest.mark.asyncio
async def test_transcribe_english_audio(async_client: httpx.AsyncClient):
    """Tests the /transcribe endpoint with the English audio file."""
    test_file = Path(enTestFile)
    
    try:
        with open_audio_file(test_file) as f:
            files = {"audio_file": (test_file.name, f, "audio/mp3")}

            response = await async_client.post(
                "/transcribe",
                files=files,
                headers={"Authorization": TEST_TOKEN}
            )
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {e}")
        return

    assert response.status_code == 200
    response_json = response.json()
    assert "transcript" in response_json
    assert isinstance(response_json["transcript"], str)

    actual_transcript = response_json["transcript"].strip()
    assert actual_transcript == EXPECTED_ENGLISH_TRANSCRIPT.strip()


# --- Test Transcription for Farsi Audio ---
@pytest.mark.asyncio
async def test_transcribe_farsi_audio(async_client: httpx.AsyncClient):
    """Tests the /transcribe endpoint with the Farsi audio file."""
    test_file = Path(faTestFile)
    try:
        with open_audio_file(test_file) as f:
            files = {"audio_file": (test_file.name, f, "audio/mp3")}

            response = await async_client.post(
                "/transcribe",
                files=files,
                headers={"Authorization": TEST_TOKEN}
            )
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {e}")
        return

    assert response.status_code == 200
    response_json = response.json()
    assert "transcript" in response_json
    assert isinstance(response_json["transcript"], str)


    actual_transcript = response_json["transcript"].strip()
    assert actual_transcript == EXPECTED_FARSI_TRANSCRIPT.strip()


# --- Test Transcribe and Diarize endpoint
@pytest.mark.asyncio
async def test_transcribe_and_diarize_audio(async_client: httpx.AsyncClient):
    """Tests the /transcribe_and_diarize endpoint with an audio file."""

    # Switch this later to a file with multiple speakers
    # Waiting for ghazal to send more test audios
    audio_file_to_test = Path(enTestFile)

    try:
        with open_audio_file(audio_file_to_test) as f:
            files = {"audio_file": (audio_file_to_test.name, f, "audio/mp3")}

            response = await async_client.post(
                "/transcribe_and_diarize",
                files=files,
                headers={"Authorization": TEST_TOKEN}
            )
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {e}")
        return


    assert response.status_code == 200
    response_json = response.json()
    assert "segments" in response_json
    assert isinstance(response_json["segments"], list)

    # Basic check for segment structure
    if response_json["segments"]:
       first_segment = response_json["segments"][0]
       assert "speaker" in first_segment
       assert "start" in first_segment
       assert "end" in first_segment
       assert "text" in first_segment
       assert isinstance(first_segment["start"], (int, float))
       assert isinstance(first_segment["end"], (int, float))
       assert isinstance(first_segment["text"], str)
       assert isinstance(first_segment["speaker"], str)


    # Reconstruct the full text from segments and compare it
    # to the expected transcript, ignoring speaker/timestamp details.
    actual_combined_text_from_segments = " ".join([
        seg.get("text", "").strip() for seg in response_json["segments"]
        if isinstance(seg, dict) and "text" in seg
    ])

    # If testing with the English audio file, compare to the expected English transcript??
    # Idk if we need this??
    if audio_file_to_test == enTestFile:
         assert actual_combined_text_from_segments.strip() == EXPECTED_ENGLISH_TRANSCRIPT.strip()


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


    
    assert isinstance(summary_data, dict)
    
    assert "main_topic" in summary_data
    assert "summary" in summary_data
    assert "key_points" in summary_data
    assert "tasks_to_complete" in summary_data
    assert isinstance(summary_data["main_topic"], str)
    assert isinstance(summary_data["summary"], str)
    assert isinstance(summary_data["key_points"], list)
    assert isinstance(summary_data["tasks_to_complete"], list)


# Test authentication failure
@pytest.mark.asyncio
async def test_auth_failure(async_client: httpx.AsyncClient):
    """Tests that endpoints return 401 without correct authorization."""

    response_no_header = await async_client.post("/transcribe", files={})
    assert response_no_header.status_code == 401

    response_wrong_token = await async_client.post(
        "/transcribe",
        files={},
        headers={"Authorization": "Bearer wrong_token"}
    )
    assert response_wrong_token.status_code == 401

    response_td_no_header = await async_client.post("/transcribe_and_diarize", files={})
    assert response_td_no_header.status_code == 401

    response_sum_no_header = await async_client.post("/summarize", json={})
    assert response_sum_no_header.status_code == 401

    response_sum_wrong_token = await async_client.post(
         "/summarize",
         json=create_dummy_merged_segments(),
         headers={"Authorization": "Bearer wrong_token"}
    )
    assert response_sum_wrong_token.status_code == 401