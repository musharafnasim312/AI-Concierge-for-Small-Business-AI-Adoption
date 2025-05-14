from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio
from collections import defaultdict

class Task(BaseModel):
    """Task model for the in-memory task manager"""
    title: str
    when: str
    description: str
    created_at: datetime = datetime.now()
    completed: bool = False

class TaskManager:
    """In-memory task management system"""
    
    def __init__(self):
        # Using defaultdict to store tasks per user
        self._tasks: Dict[str, List[Task]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def add_task(self, user_id: str, task: Dict) -> Task:
        """
        Add a new task for a user
        
        Args:
            user_id: Unique identifier for the user
            task: Task details including title, when, and description
            
        Returns:
            Created Task object
        """
        async with self._lock:
            new_task = Task(**task)
            self._tasks[user_id].append(new_task)
            return new_task
    
    async def list_tasks(self, user_id: str) -> List[Task]:
        """
        List all tasks for a user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of Task objects
        """
        async with self._lock:
            return self._tasks.get(user_id, [])
    
    async def complete_task(self, user_id: str, task_title: str) -> Optional[Task]:
        """
        Mark a task as completed
        
        Args:
            user_id: Unique identifier for the user
            task_title: Title of the task to complete
            
        Returns:
            Updated Task object or None if not found
        """
        async with self._lock:
            for task in self._tasks[user_id]:
                if task.title == task_title:
                    task.completed = True
                    return task
            return None
    
    async def remove_task(self, user_id: str, task_title: str) -> bool:
        """
        Remove a task
        
        Args:
            user_id: Unique identifier for the user
            task_title: Title of the task to remove
            
        Returns:
            True if task was removed, False otherwise
        """
        async with self._lock:
            tasks = self._tasks[user_id]
            for i, task in enumerate(tasks):
                if task.title == task_title:
                    tasks.pop(i)
                    return True
            return False

# Global task manager instance
task_manager = TaskManager()
