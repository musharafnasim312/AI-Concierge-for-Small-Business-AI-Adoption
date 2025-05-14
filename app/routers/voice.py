from fastapi import APIRouter, File, UploadFile, Depends
from fastapi.responses import StreamingResponse
import speech_recognition as sr
import pyttsx3
import io
import tempfile
import os
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .auth import get_current_user
from .concierge import chat

router = APIRouter()
executor = ThreadPoolExecutor()

async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Transcribe audio file to text using Whisper
    
    Args:
        audio_file: Uploaded audio file
        
    Returns:
        Transcribed text
    """
    recognizer = sr.Recognizer()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        # Write uploaded file to temporary file
        temp_file.write(await audio_file.read())
        temp_file.flush()
        
        # Use speech recognition
        with sr.AudioFile(temp_file.name) as source:
            audio = recognizer.record(source)
            
        try:
            # Try using Whisper first
            text = recognizer.recognize_whisper(audio)
        except:
            # Fallback to Google Speech Recognition
            text = recognizer.recognize_google(audio)
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return text

def text_to_speech(text: str) -> bytes:
    """
    Convert text to speech using pyttsx3
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Audio bytes
    """
    engine = pyttsx3.init()
    
    # Save to bytes buffer
    with io.BytesIO() as buffer:
        engine.save_to_file(text, buffer)
        engine.runAndWait()
        audio_data = buffer.getvalue()
    
    return audio_data

@router.post("/voice")
async def voice_endpoint(
    audio: UploadFile = File(...),
    username: str = Depends(get_current_user)
) -> StreamingResponse:
    """
    Voice interface endpoint
    
    Args:
        audio: Uploaded audio file
        username: Authenticated username
        
    Returns:
        Audio response
    """
    # Transcribe audio to text
    text = await transcribe_audio(audio)
    
    # Get chat response
    chat_response = await chat(message={"message": text, "stream": False}, username=username)
    
    # Convert response to speech
    loop = asyncio.get_event_loop()
    audio_data = await loop.run_in_executor(executor, text_to_speech, chat_response.response)
    
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav"
    )
