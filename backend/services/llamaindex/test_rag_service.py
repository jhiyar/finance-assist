"""
Test script for the LlamaIndex RAG Service.
"""
import os
import sys
import logging
from typing import List

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_assist.settings')
import django
django.setup()

from llama_index.core import Document
from .rag_service import get_llamaindex_rag_service, setup_llamaindex_rag_service
from .document_loader import get_llamaindex_document_loader, create_sample_documents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_document_loading():
    """Test document loading functionality."""
    print("=" * 60)
    print("TESTING DOCUMENT LOADING")
    print("=" * 60)
    
    try:
        loader = get_llamaindex_document_loader()
        
        # Test sample document creation
        print("\n1. Creating sample AI documents...")
        ai_docs = loader.create_sample_ai_documents()
        print(f"Created {len(ai_docs)} AI documents")
        
        print("\n2. Creating sample finance documents...")
        finance_docs = loader.create_sample_finance_documents()
        print(f"Created {len(finance_docs)} finance documents")
        
        # Combine documents
        all_docs = ai_docs + finance_docs
        print(f"\nTotal documents: {len(all_docs)}")
        
        # Show sample document
        if all_docs:
            print(f"\nSample document:")
            print(f"Text: {all_docs[0].text[:100]}...")
            print(f"Metadata: {all_docs[0].metadata}")
        
        return all_docs
        
    except Exception as e:
        print(f"Document loading test failed: {e}")
        return []


def test_vector_retriever(rag_service, documents):
    """Test Vector Index Retriever."""
    print("\n" + "=" * 60)
    print("TESTING VECTOR INDEX RETRIEVER")
    print("=" * 60)
    
    try:
        # Load documents
        rag_service.load_documents(documents)
        
        # Test retriever
        print("\n1. Testing Vector Retriever...")
        retriever = rag_service.get_vector_retriever(similarity_top_k=3)
        results = rag_service.search_with_retriever("vector", "What is machine learning?", similarity_top_k=3)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        # Test query engine
        print("\n2. Testing Vector Query Engine...")
        response = rag_service.query_with_engine("vector", "What is machine learning?", similarity_top_k=3)
        print(f"Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Vector retriever test failed: {e}")
        return False


def test_bm25_retriever(rag_service, documents):
    """Test BM25 Retriever."""
    print("\n" + "=" * 60)
    print("TESTING BM25 RETRIEVER")
    print("=" * 60)
    
    try:
        # Test retriever
        print("\n1. Testing BM25 Retriever...")
        retriever = rag_service.get_bm25_retriever(similarity_top_k=3)
        results = rag_service.search_with_retriever("bm25", "machine learning algorithms", similarity_top_k=3)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        # Test query engine
        print("\n2. Testing BM25 Query Engine...")
        response = rag_service.query_with_engine("bm25", "machine learning algorithms", similarity_top_k=3)
        print(f"Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"BM25 retriever test failed: {e}")
        return False


def test_document_summary_retriever(rag_service, documents):
    """Test Document Summary Retriever."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT SUMMARY RETRIEVER")
    print("=" * 60)
    
    try:
        # Test LLM-based retriever
        print("\n1. Testing Document Summary LLM Retriever...")
        retriever = rag_service.get_document_summary_retriever("llm", top_k=2)
        results = rag_service.search_with_retriever("document_summary_llm", "What are the different types of learning?", top_k=2)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        # Test embedding-based retriever
        print("\n2. Testing Document Summary Embedding Retriever...")
        retriever = rag_service.get_document_summary_retriever("embedding", top_k=2)
        results = rag_service.search_with_retriever("document_summary_embedding", "What are the different types of learning?", top_k=2)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"Document summary retriever test failed: {e}")
        return False


def test_auto_merging_retriever(rag_service, documents):
    """Test Auto Merging Retriever."""
    print("\n" + "=" * 60)
    print("TESTING AUTO MERGING RETRIEVER")
    print("=" * 60)
    
    try:
        # Test retriever
        print("\n1. Testing Auto Merging Retriever...")
        retriever = rag_service.get_auto_merging_retriever(chunk_sizes=[256, 128, 64], similarity_top_k=4)
        results = rag_service.search_with_retriever("auto_merging", "How do neural networks work?", chunk_sizes=[256, 128, 64], similarity_top_k=4)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"Auto merging retriever test failed: {e}")
        return False


def test_recursive_retriever(rag_service, documents):
    """Test Recursive Retriever."""
    print("\n" + "=" * 60)
    print("TESTING RECURSIVE RETRIEVER")
    print("=" * 60)
    
    try:
        # Test retriever
        print("\n1. Testing Recursive Retriever...")
        retriever = rag_service.get_recursive_retriever(reference_strategy="cross_document", similarity_top_k=2)
        results = rag_service.search_with_retriever("recursive", "What are AI applications?", reference_strategy="cross_document", similarity_top_k=2)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"Recursive retriever test failed: {e}")
        return False


def test_query_fusion_retriever(rag_service, documents):
    """Test Query Fusion Retriever."""
    print("\n" + "=" * 60)
    print("TESTING QUERY FUSION RETRIEVER")
    print("=" * 60)
    
    try:
        # Test retriever
        print("\n1. Testing Query Fusion Retriever (RRF mode)...")
        retriever = rag_service.get_query_fusion_retriever(mode="reciprocal_rerank", similarity_top_k=3, num_queries=3)
        results = rag_service.search_with_retriever("query_fusion", "What are the main approaches to machine learning?", mode="reciprocal_rerank", similarity_top_k=3, num_queries=3)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        # Test query engine
        print("\n2. Testing Query Fusion Query Engine...")
        response = rag_service.query_with_engine("query_fusion", "What are the main approaches to machine learning?", mode="reciprocal_rerank", similarity_top_k=3, num_queries=3)
        print(f"Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Query fusion retriever test failed: {e}")
        return False


def test_adaptive_fusion_retriever(rag_service, documents):
    """Test Adaptive Query Fusion Retriever."""
    print("\n" + "=" * 60)
    print("TESTING ADAPTIVE QUERY FUSION RETRIEVER")
    print("=" * 60)
    
    try:
        # Test retriever
        print("\n1. Testing Adaptive Query Fusion Retriever...")
        retriever = rag_service.get_adaptive_query_fusion_retriever(similarity_top_k=3, num_queries=3)
        results = rag_service.search_with_retriever("adaptive_fusion", "List all types of learning algorithms", similarity_top_k=3, num_queries=3)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"Adaptive fusion retriever test failed: {e}")
        return False


def test_service_info(rag_service):
    """Test service information."""
    print("\n" + "=" * 60)
    print("TESTING SERVICE INFORMATION")
    print("=" * 60)
    
    try:
        info = rag_service.get_service_info()
        print("Service Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print(f"\nAvailable retrievers: {rag_service.get_available_retrievers()}")
        print(f"Available engines: {rag_service.get_available_engines()}")
        
        return True
        
    except Exception as e:
        print(f"Service info test failed: {e}")
        return False


def main():
    """Main test function."""
    print("LlamaIndex RAG Service Test Suite")
    print("=" * 60)
    
    # Test document loading
    documents = test_document_loading()
    if not documents:
        print("Failed to load documents. Exiting.")
        return
    
    # Create RAG service
    try:
        rag_service = get_llamaindex_rag_service("test_collection")
        print(f"\nRAG Service created successfully")
    except Exception as e:
        print(f"Failed to create RAG service: {e}")
        return
    
    # Run tests
    test_results = []
    
    # Test service info
    test_results.append(("Service Info", test_service_info(rag_service)))
    
    # Test retrievers
    test_results.append(("Vector Retriever", test_vector_retriever(rag_service, documents)))
    test_results.append(("BM25 Retriever", test_bm25_retriever(rag_service, documents)))
    test_results.append(("Document Summary Retriever", test_document_summary_retriever(rag_service, documents)))
    test_results.append(("Auto Merging Retriever", test_auto_merging_retriever(rag_service, documents)))
    test_results.append(("Recursive Retriever", test_recursive_retriever(rag_service, documents)))
    test_results.append(("Query Fusion Retriever", test_query_fusion_retriever(rag_service, documents)))
    test_results.append(("Adaptive Fusion Retriever", test_adaptive_fusion_retriever(rag_service, documents)))
    
    # Print results summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    main()
