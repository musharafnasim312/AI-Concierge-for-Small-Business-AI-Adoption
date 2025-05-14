"""Tests for the RAG (Retrieval Augmented Generation) system"""
import pytest
from ..models.rag import RAGSystem
from ..tools.retrieve_docs import DocumentRetriever, Document, RetrievalResult

@pytest.fixture
def rag_system():
    """Create a test RAG system instance"""
    return RAGSystem("test_kb.json")

@pytest.fixture
def doc_retriever():
    """Create a test document retriever instance"""
    return DocumentRetriever()

@pytest.mark.asyncio
async def test_rag_retrieval(rag_system):
    """Test document retrieval and scoring"""
    result = await rag_system.retrieve_and_grade("What is machine learning?")
    assert result.factual_relevance >= 0.0
    assert result.factual_relevance <= 1.0
    assert result.answer_coverage >= 0.0
    assert result.answer_coverage <= 1.0
    assert len(result.documents) > 0

@pytest.mark.asyncio
async def test_out_of_scope_query(rag_system):
    """Test handling of out-of-scope queries"""
    result = await rag_system.retrieve_and_grade("How do I set up payroll software?")
    assert result.factual_relevance < 0.6
    assert result.answer_coverage < 0.6

@pytest.mark.asyncio
async def test_query_refinement(rag_system):
    """Test query refinement process"""
    initial_result = await rag_system.retrieve_and_grade("payroll setup")
    refined_result = await rag_system.refine_and_retry("payroll setup", initial_result)
    assert refined_result.query != "payroll setup"
    assert isinstance(refined_result, RetrievalResult)

@pytest.mark.asyncio
async def test_source_citations(doc_retriever):
    """Test source citation format"""
    result = await doc_retriever.retrieve_docs("AI technology")
    for doc in result.docs:
        assert isinstance(doc, Document)
        assert doc.source != ""
        assert isinstance(doc.metadata, dict)

@pytest.mark.asyncio
async def test_relevance_threshold(rag_system):
    """Test relevance threshold behavior"""
    result = await rag_system.retrieve_and_grade("What is deep learning?")
    assert result.factual_relevance >= 0.6 or result.response == "My knowledge base doesn't cover that topic."

@pytest.mark.asyncio
async def test_multiple_sources(doc_retriever):
    """Test retrieval from multiple sources"""
    result = await doc_retriever.retrieve_docs("neural networks")
    assert len(result.docs) > 1
    sources = {doc.source for doc in result.docs}
    assert len(sources) > 1
