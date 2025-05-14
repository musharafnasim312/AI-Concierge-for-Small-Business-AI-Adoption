from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings
from openai import AsyncOpenAI
from pydantic import BaseModel
import os

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class Document(BaseModel):
    """Document model for retrieved content"""
    content: str
    source: str
    metadata: Optional[Dict] = None

class RetrievalResult(BaseModel):
    """Result model for document retrieval"""
    query: str
    docs: List[Document]

class DocumentRetriever:
    """RAG-powered document retrieval using ChromaDB"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("knowledge_base")
    
    async def retrieve_docs(self, query: str) -> RetrievalResult:
        """
        Retrieve relevant documents based on the query
        
        Args:
            query: User's question
            
        Returns:
            RetrievalResult containing query and relevant documents
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=3
        )
        
        docs = []
        for idx, doc in enumerate(results['documents'][0]):
            docs.append(Document(
                content=doc,
                source=results['metadatas'][0][idx].get('source', 'Unknown'),
                metadata=results['metadatas'][0][idx]
            ))
        
        return RetrievalResult(query=query, docs=docs)
    
    async def grade_retrieval(self, question: str, docs: List[Document]) -> Dict[str, float]:
        """
        Grade the retrieval results using GPT-4
        
        Args:
            question: Original user question
            docs: Retrieved documents
            
        Returns:
            Dict containing factual_relevance and answer_coverage scores
        """
        prompt = f"""Rate the following on a scale of 0-1:

Question: {question}
Retrieved Documents: {[doc.content for doc in docs]}

Factual Relevance: [0-1]
Answer Coverage: [0-1]"""

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        
        # Parse scores from response
        content = response.choices[0].message.content
        relevance = float([line for line in content.split('\n') if 'Factual Relevance' in line][0].split(':')[1].strip())
        coverage = float([line for line in content.split('\n') if 'Answer Coverage' in line][0].split(':')[1].strip())
        
        return {
            "factual_relevance": relevance,
            "answer_coverage": coverage
        }

# Create global RAG system instance
rag_system = DocumentRetriever()
