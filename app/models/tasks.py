from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TaskCreate(BaseModel):
    """Task creation model"""
    title: str
    when: str
    description: str

class Task(TaskCreate):
    """Task model with additional fields"""
    created_at: datetime = datetime.now()
    completed: bool = False

class TaskList(BaseModel):
    """Task list response model"""
    tasks: List[Task]

class TaskResponse(BaseModel):
    """Task operation response model"""
    status: str
    task: Optional[Task] = None
    message: Optional[str] = None
