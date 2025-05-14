# AI Concierge for Small-Business AI Adoption

A FastAPI-based intelligent concierge system that answers questions about AI technologies, schedules demo calls, and maintains task lists with self-grading and adaptive learning capabilities. The system uses RAG (Retrieval Augmented Generation) for accurate information retrieval and includes a sophisticated self-reflection mechanism.

## Features

- 🔍 Advanced RAG System with Vector Search
  - Real-time document retrieval
  - Source citations in responses
  - Automatic query refinement
  - Self-grading mechanism (0-1 scale)

- 📅 Intelligent Task Management
  - Demo scheduling
  - To-do list management
  - Task completion tracking

- 🎯 Self-Grading System
  - Factual relevance scoring
  - Answer coverage evaluation
  - Threshold-based refinement
  - Performance logging

- 🔄 Self-Reflection & Adaptation
  - User feedback integration
  - Score decay mechanism
  - Adaptive system prompts
  - Session memory management

- 🔐 Security & Performance
  - JWT authentication
  - Rate limiting (30 req/min)
  - Async implementation
  - Docker containerization

- 🎤 Voice Interface (Bonus)
  - Speech-to-text conversion
  - Text-to-speech response
  - Multiple engine support

## Technical Architecture

### Core Components

1. **RAG System Implementation**
   ```python
   class RAGSystem:
       def retrieve_docs(query: str) -> List[Document]:
           # Vector search over knowledge base
           # Returns: {docs: [{content, source, metadata}], query}

       def self_grade(query: str, docs: List[Document]) -> GradingResult:
           # Grades relevance and coverage (0-1 scale)
           # Threshold: 0.6 for both metrics
   ```

2. **Task Management**
   ```python
   class TaskManager:
       def add_task(task: Dict) -> Task:
           # {title: str, when: str, description: str}

       def list_tasks() -> List[Task]:
           # Returns all current tasks
   ```

3. **Self-Reflection System**
   ```python
   class FeedbackSystem:
       def process_feedback(type: str) -> float:
           # type: 'good_answer' | 'bad_answer'
           # Updates score with decay (0.5 per turn)

       def get_system_prompt(score: float) -> str:
           # Adapts prompt based on cumulative score
   ```

## Environment Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for non-Docker setup)
- For voice features:
  - Linux: `portaudio19-dev`, `python3-pyaudio`, `espeak`
  - Windows: PyAudio wheel from official sources

### Quick Start with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-concierge
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

3. **Build and run services**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   curl http://localhost:8000/health
   ```

### Manual Setup (Alternative)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Testing Guide

### 1. Authentication Flow

```bash
# Register a new user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "password123"}'

# Login and get JWT token
curl -X POST http://localhost:8000/login \
  -F "username=demo" \
  -F "password=password123"
```

### 2. Chat Interactions

```bash
# Basic question with citations
curl -X POST http://localhost:8000/concierge/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is few-shot learning?", "stream": false}'

# Out-of-scope question handling
curl -X POST http://localhost:8000/concierge/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I set up payroll software?", "stream": false}'
```

### 3. Task Management

```bash
# Schedule a demo
curl -X POST http://localhost:8000/concierge/tasks \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Demo Call",
    "when": "2025-05-20T15:00:00",
    "description": "Demo of AI capabilities"
  }'

# List all tasks
curl -X GET http://localhost:8000/concierge/tasks \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Feedback Commands

```bash
# Positive feedback
curl -X POST http://localhost:8000/concierge/feedback \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feedback_type": "good_answer"}'

# Negative feedback
curl -X POST http://localhost:8000/concierge/feedback \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feedback_type": "bad_answer"}'
```

### 5. Voice Interface

```bash
# Send audio and get text response
curl -X POST http://localhost:8000/concierge/voice \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@question.wav"

# Get audio response
curl -X POST http://localhost:8000/concierge/voice \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@question.wav" \
  -F "return_audio=true"
```

## Self-Grading Mechanism

### Rubric Explanation

1. **Factual Relevance (0-1)**
   - 0.8-1.0: Perfect match to query
   - 0.6-0.8: Good relevance with minor gaps
   - 0.4-0.6: Partially relevant
   - 0.0-0.4: Poor relevance

2. **Answer Coverage (0-1)**
   - 0.8-1.0: Complete answer possible
   - 0.6-0.8: Most aspects covered
   - 0.4-0.6: Partial coverage
   - 0.0-0.4: Insufficient coverage

### Threshold Justification

- **Threshold Level: 0.6**
  - Balances precision with recall
  - Allows for partial matches while filtering irrelevant content
  - Empirically tested for optimal user experience

### Query Refinement Process

1. Initial query → Vector search
2. Score results (relevance & coverage)
3. If score < 0.6:
   - Generate refined query
   - Repeat search once
   - If still below threshold, acknowledge knowledge gap

## Self-Reflection Algorithm

### Score Calculation
```python
def calculate_feedback_score(current_score: float, feedback_type: str) -> float:
    decay_factor = 0.5
    feedback_value = 1 if feedback_type == "good_answer" else -1
    return (current_score * decay_factor) + feedback_value
```

### Decay Mechanism
- Score decays by 50% each turn
- Prevents score accumulation
- Maintains recency bias
- Example sequence:
  ```
  Turn 1: bad_answer  → -1.0
  Turn 2: (no feedback) → -0.5
  Turn 3: good_answer → +0.75
  Turn 4: (no feedback) → +0.375
  ```

### Prompt Adaptation
- Cumulative score < 0:
  ```
  Be more concise and cite sources explicitly.
  Focus on factual information.
  ```
- Cumulative score > 0:
  ```
  Maintain current style and detail level.
  User finds responses helpful.
  ```

## Testing Suite

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest app/tests/test_concierge.py

# Run with coverage
python -m pytest --cov=app
### Test Categories

1. **Unit Tests**
   - RAG system functionality
   - Self-grading mechanism
   - Task management operations
   - Feedback processing

2. **Integration Tests**
   - API endpoints
   - Authentication flow
   - Database interactions
   - Voice processing

3. **Example Test Cases**
   ```python
   def test_self_grading():
       rag = RAGSystem("test_kb.json")
       result = rag.retrieve_and_grade("What is machine learning?")
       assert result.factual_relevance >= 0.6
       assert result.answer_coverage >= 0.6

   def test_feedback_decay():
       feedback = FeedbackSystem()
       score = feedback.process("good_answer")  # 1.0
       score = feedback.apply_decay(score)     # 0.5
       assert score == 0.5
   ```

## Deployment

### GitHub Setup

1. **Initialize Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Configure Sensitive Data**
   - Copy `.env.example` to `.env`
   - Add your actual credentials to `.env`
   - Verify `.env` is in `.gitignore`

3. **Required Environment Variables**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   JWT_SECRET=your_jwt_secret_here
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ALGORITHM=HS256
   ```

4. **Push to GitHub**
   ```bash
   git remote add origin <your-github-repo-url>
   git branch -M main
   git push -u origin main
   ```

### Security Notes

- Never commit `.env` file
- Keep API keys and secrets secure
- Use environment variables for credentials
- Review `.gitignore` before pushing

## License

MIT License - See LICENSE file for details

## Self-Grading System

The RAG reliability system uses GPT-4 to grade retrieved documents:

1. Grading Criteria:
   - Factual Relevance [0-1]: Measures how well documents match the query
   - Answer Coverage [0-1]: Assesses completeness of potential answer

2. Thresholds (0.6):
   - Chosen to balance precision vs. recall
   - Below threshold triggers query refinement
   - Two failed attempts result in knowledge gap admission

3. Query Refinement:
   - Uses GPT-4 to reformulate search terms
   - Maximum one refinement attempt
   - Logs all scores for quality monitoring

## Self-Reflection Algorithm

1. Feedback Scoring:
   - Positive feedback (/good_answer): +1
   - Negative feedback (/bad_answer): -1

2. Decay Mechanism:
   - Score *= 0.5 after each user message
   - Prevents score accumulation
   - Example progression:
     ```
     Turn 1: Bad answer (-1)
     Turn 2: Score decays to -0.5
     Turn 3: Good answer (-0.5 + 1 = 0.5)
     Turn 4: Score decays to 0.25
     ```

3. Adaptive Behavior:
   - Negative cumulative score: "Be more concise and cite sources explicitly"
   - Positive/Zero score: Standard conversational style

## Testing

Run tests:
```bash
docker-compose run web pytest
```

Tests cover:
- Unit tests for all core components
- Integration tests for API endpoints
- RAG reliability testing
- Memory management validation
