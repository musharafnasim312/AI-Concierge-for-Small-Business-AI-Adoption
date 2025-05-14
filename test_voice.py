import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
import wave
import time

def record_audio(duration=5, fs=16000):
    """Record audio from microphone"""
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return recording

def save_audio(audio_data, filename="test_input.wav", fs=16000):
    """Save audio data to WAV file"""
    sf.write(filename, audio_data, fs)
    return filename

def play_audio(filename):
    """Play audio file"""
    data, fs = sf.read(filename)
    print("Playing response...")
    sd.play(data, fs)
    sd.wait()

def main():
    # 1. Record audio
    audio_data = record_audio()
    input_file = save_audio(audio_data)
    
    # 2. Send to API
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc0NzI0MDE5N30.EzYsyXO0tO8guMqaKTGnsJVltqpCVD8z9w84f0PWzZY"
    url = "http://127.0.0.1:8000/concierge/voice"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(input_file, "rb") as f:
        files = {"audio": ("input.wav", f, "audio/wav")}
        print("Sending to API...")
        response = requests.post(url, headers=headers, files=files)
    
    # 3. Save and play response
    if response.status_code == 200:
        output_file = "response.wav"
        with open(output_file, "wb") as f:
            f.write(response.content)
        print("Got response, playing...")
        play_audio(output_file)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
