from pydantic import BaseModel
from typing import List, Dict, Optional
import json
from difflib import SequenceMatcher

class Document(BaseModel):
    """Document model for retrieved content"""
    content: str
    source: str
    metadata: Optional[Dict] = None

class RetrievalResult(BaseModel):
    """Result model for document retrieval"""
    query: str
    docs: List[Document]

class GradingResult(BaseModel):
    """Result model for self-grading"""
    factual_relevance: float
    answer_coverage: float
    refined_query: Optional[str] = None

class RAGSystem:
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)
    
    def _load_knowledge_base(self, path: str) -> List[Dict]:
        with open(path, 'r') as f:
            data = json.load(f)
            return data['documents']
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        # Convert to lowercase and split into terms
        query_terms = set(query.lower().split())
        text_terms = set(text.lower().split())
        
        # Calculate term overlap
        overlap = len(query_terms & text_terms)
        if overlap == 0:
            return 0
        
        # Calculate Jaccard similarity
        jaccard = len(query_terms & text_terms) / len(query_terms | text_terms)
        
        # Calculate sequence similarity
        sequence_sim = SequenceMatcher(None, query.lower(), text.lower()).ratio()
        
        # Combine both metrics
        return max(jaccard, sequence_sim)
    
    async def retrieve_docs(self, query: str, k: int = 3) -> RetrievalResult:
        # Calculate similarity scores for each document
        scored_docs = []
        for doc in self.knowledge_base:
            # Calculate similarity with full query
            full_sim = self._calculate_similarity(query, doc['content'])
            
            # Calculate similarity with metadata topics
            topic_sim = max(
                self._calculate_similarity(query, topic)
                for topic in [doc.get('metadata', {}).get('topic', ''), doc.get('metadata', {}).get('subtopic', '')]
            )
            
            # Use the maximum similarity score
            scored_docs.append((doc, max(full_sim, topic_sim)))
        
        # Sort by similarity score and take top k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = scored_docs[:k]
        
        return RetrievalResult(
            query=query,
            docs=[
                Document(
                    content=doc['content'],
                    source=doc['source'],
                    metadata=doc.get('metadata', {})
                )
                for doc, score in top_docs
                if score > 0.05  # Lower threshold for relevance
            ]
        )
    
    async def grade_retrieval(self, question: str, result: RetrievalResult) -> GradingResult:
        # Simple grading based on keyword matching
        question_terms = set(question.lower().split())
        
        # Calculate relevance based on term overlap
        relevance_scores = []
        for doc in result.docs:
            doc_terms = set(doc.content.lower().split())
            overlap = len(question_terms & doc_terms) / len(question_terms)
            relevance_scores.append(overlap)
        
        relevance = max(relevance_scores) if relevance_scores else 0
        coverage = sum(1 for score in relevance_scores if score > 0.3) / 3
        
        return GradingResult(
            factual_relevance=relevance,
            answer_coverage=coverage
        )
