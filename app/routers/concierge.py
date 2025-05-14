from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.responses import StreamingResponse
import speech_recognition as sr
import pyttsx3
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from typing import Optional, Dict, List, Union
from datetime import datetime
import json
from openai import AsyncOpenAI
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

from ..dependencies import get_current_user
from ..tools.manage_tasks import task_manager
from ..tools.retrieve_docs import rag_system

from ..core.config import settings
from ..models.rag import RAGSystem
from ..core.reflection import reflection
from .auth import get_current_user, create_access_token

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
executor = ThreadPoolExecutor()

# Initialize RAG system
rag_system = RAGSystem('knowledge_base.json')

# Session memory store
session_memory = {}

class ChatMessage(BaseModel):
    """Chat message model for user input
    
    Attributes:
        message: The user's message text
        stream: Whether to stream the response or return it as a single response
    """
    message: str
    stream: bool = False

class ChatResponse(BaseModel):
    """Chat response model for AI responses
    
    Attributes:
        response: The AI's response text
        sources: List of source documents used for the response
        feedback_score: Current feedback score affecting response style
    """
    response: str
    sources: Optional[List[Dict[str, str]]] = None
    feedback_score: Optional[float] = None

class TaskRequest(BaseModel):
    """Task creation request model
    
    Attributes:
        title: Title of the task
        when: When the task should be completed (datetime string)
        description: Detailed description of the task
    """
    title: str
    when: str
    description: str
    description: str

class TaskResponse(BaseModel):
    """Response model for task operations"""
    status: str
    task: Optional[Dict] = None
    tasks: Optional[List[Dict]] = None
    message: str

@router.post("/chat", response_model=None)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    message: ChatMessage,
    username: str = Depends(get_current_user)
):
    """Main chat endpoint for the AI concierge
    
    Args:
        request: FastAPI request object
        message: User's chat message
        username: Authenticated username
    
    Returns:
        Either a streaming response or a complete chat response
        
    Raises:
        HTTPException: If rate limit exceeded or invalid request
    """
    # Initialize or get user session
    if username not in session_memory:
        session_memory[username] = {
            "history": [],
            "feedback_score": 0,
            "last_interaction": datetime.now()
        }
    else:
        # Apply feedback score decay (0.5 per turn)
        session_memory[username]["feedback_score"] *= 0.5
        session_memory[username]["last_interaction"] = datetime.now()
    
    # Check for task-related commands
    msg = message.message.lower()
    if "schedule" in msg or "demo" in msg:
        # Extract date/time using simple pattern matching
        # In production, use a proper datetime parser
        import re
        when_pattern = r'(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)'
        match = re.search(when_pattern, msg.lower())
        if match:
            day, time = match.groups()
            task = {
                "title": "AI Demo",
                "when": f"{day} {time}",
                "description": "Scheduled AI technology demonstration"
            }
            await task_manager.add_task(username, task)
            return ChatResponse(
                response=f"Demo scheduled for {day} at {time}",
                sources=None,
                feedback_score=session_memory[username]["feedback_score"]
            )
    
    elif msg == "what do i have scheduled?" or msg == "list tasks":
        tasks = await task_manager.list_tasks(username)
        if tasks:
            task_list = "\n".join([f"{i+1}. {t.title} - {t.when}" for i, t in enumerate(tasks)])
            return ChatResponse(
                response=f"Your scheduled tasks:\n{task_list}",
                sources=None,
                feedback_score=session_memory[username]["feedback_score"]
            )
        return ChatResponse(
            response="You have no tasks scheduled.",
            sources=None,
            feedback_score=session_memory[username]["feedback_score"]
        )

    """
    Args:
        message: User's message
        username: Authenticated username
        
    Returns:
        ChatResponse with AI response and optional sources
    """
    # Process the message
    try:
        # Check for feedback commands
        if message.message.startswith("/"):
            if message.message == "/good_answer":
                reflection.add_feedback(True)
                return ChatResponse(response="Thank you for the positive feedback!")
            elif message.message == "/bad_answer":
                reflection.add_feedback(False)
                return ChatResponse(response="I'll try to improve. Thank you for the feedback.")
        
        # Get retrieval results
        retrieval_result = await rag_system.retrieve_docs(message.message)
        
        # Grade retrieval results
        grade = await rag_system.grade_retrieval(message.message, retrieval_result)
        
        # Log scores for debugging
        print(f"Self-grading scores - Relevance: {grade.factual_relevance}, Coverage: {grade.answer_coverage}")
        
        # If we have any relevant documents, try to generate a response
        if retrieval_result.docs:
            # Generate response using retrieved documents
            prompt_modifier = reflection.get_prompt_modifier()
            BASE_PROMPT = "You are an AI concierge helping with AI technology questions. "
            system_prompt = f"{BASE_PROMPT} {prompt_modifier}"
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {message.message}\n\nContext: {[doc.content for doc in retrieval_result.docs]}"}
                ],
                stream=message.stream
            )
            
            if message.stream:
                return StreamingResponse(stream_response(response), media_type="text/event-stream")
            
            answer = response.choices[0].message.content
            sources = [{"source": doc.source, "content": doc.content[:100]} for doc in retrieval_result.docs]
            
            return ChatResponse(
                response=answer,
                sources=sources,
                feedback_score=session_memory[username]["feedback_score"]
            )
        else:
            return ChatResponse(
                response="I'm sorry, my knowledge base doesn't cover that topic adequately.",
                sources=None,
                feedback_score=session_memory[username]["feedback_score"]
            )
        
        # Generate response using retrieved documents
        prompt_modifier = reflection.get_prompt_modifier()
        BASE_PROMPT = "You are an AI concierge helping with AI technology questions. "
        system_prompt = f"{BASE_PROMPT} {prompt_modifier}"
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {message.message}\n\nContext: {[doc.content for doc in retrieval_result.docs]}"}
            ],
            stream=message.stream
        )
        
        if message.stream:
            return StreamingResponse(stream_response(response), media_type="text/event-stream")
        
        answer = response.choices[0].message.content
        sources = [{"source": doc.source, "content": doc.content[:100]} for doc in retrieval_result.docs]
        
        return ChatResponse(
            response=answer,
            sources=sources,
            feedback_score=session_memory[username]["feedback_score"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Get system prompt based on feedback score
    feedback_score = session_memory[username]["feedback_score"]
    system_prompt = "Be more concise and cite sources explicitly." if feedback_score < 0 else "Maintain current style, user is satisfied."
    
    # Prepare conversation context with retrieved documents
    docs_context = "\n\nRelevant information:\n" + "\n".join(
        f"[{doc.source}]: {doc.content}" for doc in retrieval_result.docs
    )
    
    conversation = [
        {"role": "system", "content": f"{system_prompt}\n\n{docs_context}"}
    ] + session_memory[username]["history"] + [
        {"role": "user", "content": message.message}
    ]
    
    # Get AI response
    if message.stream:
        return StreamingResponse(
            stream_response(conversation),
            media_type="text/event-stream"
        )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=conversation,
            stream=False
        )
        answer = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Update conversation history
    session_memory[username]["history"].extend([
        {"role": "user", "content": message.message},
        {"role": "assistant", "content": response.choices[0].message.content}
    ])
    
    # Keep history manageable
    if len(session_memory[username]["history"]) > 10:
        session_memory[username]["history"] = session_memory[username]["history"][-10:]
    
    return ChatResponse(
        response=response.choices[0].message.content,
        sources=[{"source": doc.source, "content": doc.content} for doc in retrieval_result.docs],
        feedback_score=session_memory[username]["feedback_score"]
    )

@router.post("/feedback/{feedback_type}")
async def handle_feedback(
    feedback_type: str,
    username: str = Depends(get_current_user)
):
    """Handle user feedback"""
    if username not in session_memory:
        raise HTTPException(status_code=404, detail="No active session")
    
    if feedback_type == "good_answer":
        session_memory[username]["feedback_score"] += 1
    elif feedback_type == "bad_answer":
        session_memory[username]["feedback_score"] -= 1
    
    return {"status": "success", "new_score": session_memory[username]["feedback_score"]}

async def refine_query(query: str) -> str:
    """Refine the query using GPT-4"""
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Refine the following query to be more specific and searchable:"},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content

async def stream_response(conversation: List[Dict[str, str]]):
    """Stream the AI response"""
    async for chunk in await client.chat.completions.create(
        model="gpt-4",
        messages=conversation,
        stream=True
    ):
        if chunk and chunk.choices[0].delta.content:
            yield f"data: {chunk.choices[0].delta.content}\n\n"

def get_system_prompt(feedback_score: float):
    """Get appropriate system prompt based on feedback score"""
    if feedback_score < 0:
        return "Be more concise and cite sources explicitly."
    return "Maintain current style, user is satisfied."

async def transcribe_audio(audio_file: UploadFile) -> str:
    """Transcribe audio file to text using speech recognition"""
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
    """Convert text to speech using pyttsx3"""
    engine = pyttsx3.init()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        # Save speech to temporary file
        engine.save_to_file(text, temp_file.name)
        engine.runAndWait()
        
        # Read audio data
        with open(temp_file.name, "rb") as f:
            audio_data = f.read()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return audio_data

@router.post("/tasks")
@limiter.limit("30/minute")
async def manage_tasks(
    task_request: TaskRequest,
    request: Request,
    username: str = Depends(get_current_user)
) -> TaskResponse:
    """Add a new task"""
    task = await task_manager.add_task(username, task_request.dict())
    return TaskResponse(
        status="success",
        task=task.dict(),
        message=f"Task '{task.title}' scheduled for {task.when}"
    )

@router.get("/tasks")
@limiter.limit("30/minute")
async def list_tasks(
    request: Request,
    username: str = Depends(get_current_user)
) -> TaskResponse:
    """List all tasks"""
    tasks = await task_manager.list_tasks(username)
    return TaskResponse(
        status="success",
        tasks=[task.dict() for task in tasks],
        message=f"Found {len(tasks)} tasks"
    )

@router.post("/tasks/{task_title}/complete")
@limiter.limit("30/minute")
async def complete_task(
    task_title: str,
    request: Request,
    username: str = Depends(get_current_user)
) -> TaskResponse:
    """Mark a task as completed"""
    task = await task_manager.complete_task(username, task_title)
    if task:
        return TaskResponse(
            status="success",
            task=task.dict(),
            message=f"Task '{task_title}' marked as completed"
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task '{task_title}' not found"
    )

@router.delete("/tasks/{task_title}")
@limiter.limit("30/minute")
async def delete_task(
    task_title: str,
    request: Request,
    username: str = Depends(get_current_user)
) -> TaskResponse:
    """Delete a task"""
    success = await task_manager.remove_task(username, task_title)
    if success:
        return TaskResponse(
            status="success",
            message=f"Task '{task_title}' deleted"
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task '{task_title}' not found"
    )

@router.post("/voice")
@limiter.limit("30/minute")
async def voice_endpoint(
    request: Request,
    audio: UploadFile = File(...),
    username: str = Depends(get_current_user)
):
    """Voice interface endpoint"""
    try:
        # Transcribe audio to text
        text = await transcribe_audio(audio)
        
        # Process through chat endpoint
        message = ChatMessage(message=text)
        chat_response = await chat(request, message, username)
        
        # Convert response to speech
        audio_data = await asyncio.get_event_loop().run_in_executor(
            executor,
            text_to_speech,
            chat_response.response
        )
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
