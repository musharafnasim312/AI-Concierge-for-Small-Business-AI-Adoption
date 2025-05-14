import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..tools.retrieve_docs import DocumentRetriever
from ..tools.manage_tasks import task_manager

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Get authentication headers"""
    # Register a test user
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_endpoint(auth_headers):
    """Test chat endpoint"""
    response = client.post(
        "/concierge/chat",
        json={"message": "How can AI help my business?"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "response" in response.json()

def test_feedback(auth_headers):
    """Test feedback mechanism"""
    response = client.post(
        "/concierge/feedback/good_answer",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["new_score"] == 1

@pytest.mark.asyncio
async def test_document_retriever():
    """Test document retrieval"""
    retriever = DocumentRetriever()
    result = await retriever.retrieve_docs("test query")
    assert result.query == "test query"
    assert isinstance(result.docs, list)

@pytest.mark.asyncio
async def test_task_manager():
    """Test task management"""
    user_id = "test_user"
    task = {
        "title": "Test Task",
        "when": "tomorrow",
        "description": "Test description"
    }
    
    # Test adding task
    new_task = await task_manager.add_task(user_id, task)
    assert new_task.title == task["title"]
    
    # Test listing tasks
    tasks = await task_manager.list_tasks(user_id)
    assert len(tasks) == 1
    assert tasks[0].title == task["title"]
    
    # Test completing task
    completed_task = await task_manager.complete_task(user_id, task["title"])
    assert completed_task.completed == True
    
    # Test removing task
    removed = await task_manager.remove_task(user_id, task["title"])
    assert removed == True
