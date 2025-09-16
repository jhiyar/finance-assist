"""
Example usage of the LlamaIndex RAG Service.
"""
import os
import sys
import logging

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, backend_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_assist.settings')
import django
django.setup()

from llama_index.core import Document
from .rag_service import get_llamaindex_rag_service
from .document_loader import get_llamaindex_document_loader, create_sample_documents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example of basic RAG service usage."""
    print("=" * 60)
    print("BASIC RAG SERVICE USAGE EXAMPLE")
    print("=" * 60)
    
    # 1. Create sample documents
    print("\n1. Creating sample documents...")
    documents = create_sample_documents("ai")
    print(f"Created {len(documents)} documents")
    
    # 2. Create RAG service
    print("\n2. Creating RAG service...")
    rag_service = get_llamaindex_rag_service("example_collection")
    
    # 3. Load documents
    print("\n3. Loading documents...")
    rag_service.load_documents(documents)
    
    # 4. Search with vector retriever
    print("\n4. Searching with vector retriever...")
    results = rag_service.search_with_retriever("vector", "What is machine learning?", similarity_top_k=3)
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.score:.4f}")
        print(f"   Text: {result.text[:100]}...")
    
    # 5. Query with vector engine
    print("\n5. Querying with vector engine...")
    response = rag_service.query_with_engine("vector", "What is machine learning?", similarity_top_k=3)
    print(f"Response: {response}")
    
    return rag_service


def example_advanced_retrievers():
    """Example of using advanced retrievers."""
    print("\n" + "=" * 60)
    print("ADVANCED RETRIEVERS EXAMPLE")
    print("=" * 60)
    
    # Create documents and service
    documents = create_sample_documents("finance")
    rag_service = get_llamaindex_rag_service("advanced_collection")
    rag_service.load_documents(documents)
    
    # 1. BM25 Retriever (if available)
    print("\n1. BM25 Retriever Example...")
    try:
        results = rag_service.search_with_retriever("bm25", "investment strategies", similarity_top_k=3)
        print(f"BM25 found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
    except Exception as e:
        print(f"BM25 not available: {e}")
    
    # 2. Document Summary Retriever
    print("\n2. Document Summary Retriever Example...")
    try:
        results = rag_service.search_with_retriever("document_summary_llm", "What is financial planning?", top_k=2)
        print(f"Document Summary found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
    except Exception as e:
        print(f"Document Summary failed: {e}")
    
    # 3. Auto Merging Retriever
    print("\n3. Auto Merging Retriever Example...")
    try:
        results = rag_service.search_with_retriever("auto_merging", "How to manage personal finances?", chunk_sizes=[256, 128, 64], similarity_top_k=4)
        print(f"Auto Merging found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
    except Exception as e:
        print(f"Auto Merging failed: {e}")
    
    # 4. Query Fusion Retriever
    print("\n4. Query Fusion Retriever Example...")
    try:
        results = rag_service.search_with_retriever("query_fusion", "What are the key components of financial planning?", mode="reciprocal_rerank", similarity_top_k=3, num_queries=3)
        print(f"Query Fusion found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
    except Exception as e:
        print(f"Query Fusion failed: {e}")


def example_query_engines():
    """Example of using query engines for end-to-end RAG."""
    print("\n" + "=" * 60)
    print("QUERY ENGINES EXAMPLE")
    print("=" * 60)
    
    # Create documents and service
    documents = create_sample_documents("ai")
    rag_service = get_llamaindex_rag_service("query_engines_collection")
    rag_service.load_documents(documents)
    
    queries = [
        "What is machine learning?",
        "Explain the difference between supervised and unsupervised learning",
        "What are neural networks used for?",
        "How does deep learning work?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        
        # Try different query engines
        engines_to_try = ["vector", "document_summary_llm", "query_fusion"]
        
        for engine_type in engines_to_try:
            try:
                response = rag_service.query_with_engine(engine_type, query, similarity_top_k=3)
                print(f"   {engine_type}: {response[:150]}...")
            except Exception as e:
                print(f"   {engine_type}: Failed - {e}")


def example_retriever_comparison():
    """Example comparing different retrievers on the same query."""
    print("\n" + "=" * 60)
    print("RETRIEVER COMPARISON EXAMPLE")
    print("=" * 60)
    
    # Create documents and service
    documents = create_sample_documents("ai")
    rag_service = get_llamaindex_rag_service("comparison_collection")
    rag_service.load_documents(documents)
    
    query = "What are the different types of machine learning?"
    
    retrievers_to_compare = [
        ("vector", {"similarity_top_k": 3}),
        ("document_summary_llm", {"top_k": 3}),
        ("auto_merging", {"chunk_sizes": [256, 128, 64], "similarity_top_k": 3}),
        ("query_fusion", {"mode": "reciprocal_rerank", "similarity_top_k": 3, "num_queries": 3})
    ]
    
    print(f"Query: {query}")
    print("\nComparing retrievers:")
    
    for retriever_type, kwargs in retrievers_to_compare:
        try:
            results = rag_service.search_with_retriever(retriever_type, query, **kwargs)
            print(f"\n{retriever_type.upper()}:")
            print(f"  Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. Score: {result.score:.4f} - {result.text[:80]}...")
        except Exception as e:
            print(f"\n{retriever_type.upper()}: Failed - {e}")


def example_service_management():
    """Example of service management features."""
    print("\n" + "=" * 60)
    print("SERVICE MANAGEMENT EXAMPLE")
    print("=" * 60)
    
    # Create service
    rag_service = get_llamaindex_rag_service("management_collection")
    
    # Load documents
    documents = create_sample_documents("finance")
    rag_service.load_documents(documents)
    
    # 1. Get service info
    print("\n1. Service Information:")
    info = rag_service.get_service_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # 2. Get available retrievers
    print(f"\n2. Available retrievers: {rag_service.get_available_retrievers()}")
    print(f"   Available engines: {rag_service.get_available_engines()}")
    
    # 3. Test a retriever
    print("\n3. Testing a retriever...")
    results = rag_service.search_with_retriever("vector", "What is investment?", similarity_top_k=2)
    print(f"   Found {len(results)} results")
    
    # 4. Clear caches
    print("\n4. Clearing caches...")
    rag_service.clear_caches()
    print("   Caches cleared")
    
    # 5. Test again (should recreate retriever)
    print("\n5. Testing after cache clear...")
    results = rag_service.search_with_retriever("vector", "What is investment?", similarity_top_k=2)
    print(f"   Found {len(results)} results")


def example_custom_documents():
    """Example of loading custom documents."""
    print("\n" + "=" * 60)
    print("CUSTOM DOCUMENTS EXAMPLE")
    print("=" * 60)
    
    # Create custom documents
    custom_documents = [
        Document(
            text="Our company policy states that all employees must complete security training annually.",
            metadata={"type": "policy", "category": "security", "department": "HR"}
        ),
        Document(
            text="The quarterly sales report shows a 15% increase in revenue compared to last quarter.",
            metadata={"type": "report", "category": "sales", "quarter": "Q3"}
        ),
        Document(
            text="New product launch scheduled for next month with focus on AI-powered features.",
            metadata={"type": "announcement", "category": "product", "timeline": "next_month"}
        )
    ]
    
    # Create service and load documents
    rag_service = get_llamaindex_rag_service("custom_collection")
    rag_service.load_documents(custom_documents)
    
    # Search with different queries
    queries = [
        "What is the company policy on security training?",
        "How did sales perform this quarter?",
        "When is the new product launching?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = rag_service.query_with_engine("vector", query, similarity_top_k=2)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Failed: {e}")


def main():
    """Main example function."""
    print("LlamaIndex RAG Service Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_usage()
        example_advanced_retrievers()
        example_query_engines()
        example_retriever_comparison()
        example_service_management()
        example_custom_documents()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
