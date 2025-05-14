from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class Task(BaseModel):
    title: str
    when: str
    description: str
    created_at: datetime = datetime.now()

class TaskManager:
    def __init__(self):
        self.tasks: List[Task] = []
    
    def add_task(self, task: Dict) -> Task:
        """Add a new task to the list"""
        new_task = Task(**task)
        self.tasks.append(new_task)
        return new_task
    
    def list_tasks(self) -> List[Task]:
        """Return all current tasks"""
        return sorted(self.tasks, key=lambda x: x.created_at)
    
    def clear_tasks(self):
        """Clear all tasks (for testing)"""
        self.tasks = []

# Global instance for in-memory storage
task_manager = TaskManager()
