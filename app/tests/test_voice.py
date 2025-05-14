import pytest
from fastapi.testclient import TestClient
import io
import wave
import numpy as np
from ..main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Get authentication headers"""
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_wav_file():
    """Create a sample WAV file for testing"""
    buffer = io.BytesIO()
    
    # Create a simple sine wave
    sample_rate = 44100
    duration = 1  # seconds
    frequency = 440  # Hz
    t = np.linspace(0, duration, int(sample_rate * duration))
    samples = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())
    
    buffer.seek(0)
    return buffer

def test_voice_endpoint(auth_headers, sample_wav_file):
    """Test voice endpoint"""
    files = {"audio": ("test.wav", sample_wav_file, "audio/wav")}
    response = client.post(
        "/concierge/voice",
        headers=auth_headers,
        files=files
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    
    # Verify response is valid WAV data
    wav_data = io.BytesIO(response.content)
    with wave.open(wav_data, 'rb') as wav:
        assert wav.getnchannels() == 1  # Mono
        assert wav.getsampwidth() == 2  # 16-bit
        assert wav.getframerate() > 0
