import pytest
from fastapi.testclient import TestClient
from main import app
import os
from pathlib import Path

from main import app

from utils.auth import TEST_TOKEN

# This worked atleast?
# TODO: Add alot of prints through out the pipelines to see progress & where it fails. 
# TODO: Fix the pyannote & mistral load up errors


@pytest.fixture(scope="session")
def test_client():
    with TestClient(app) as client:
        yield client

def test_transcribe_english_audio(test_client):
    with open("./tests/audio/test_en.mp3", "rb") as f:
        files = {"audio_file": ("test_en.mp3", f, "audio/mp3")}
        response = test_client.post("/transcribe", files=files, headers={"Authorization": TEST_TOKEN})
    assert response.status_code == 200

def test_transcribe_farsi_audio(test_client):
    with open("./tests/audio/test_fa.mp3", "rb") as f:
        files = {"audio_file": ("test_fa.mp3", f, "audio/mp3")}
        response = test_client.post("/transcribe", files=files, headers={"Authorization": TEST_TOKEN})
    assert response.status_code == 200
