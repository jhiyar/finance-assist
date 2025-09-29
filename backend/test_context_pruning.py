#!/usr/bin/env python3
"""
Test script for Context Pruning Service

This script demonstrates the context pruning functionality with sample documents
and queries to show how it works.
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_assist.settings')
django.setup()

from langchain_core.documents import Document
from services.context_pruning_service import get_context_pruning_service


def create_sample_documents():
    """Create sample documents for testing."""
    documents = [
        Document(
            page_content="""
            Financial Statement Analysis
            
            The company's revenue increased by 15% compared to the previous year.
            Operating expenses were reduced by 8% through cost optimization initiatives.
            Net profit margin improved from 12% to 14.5%.
            
            Key financial metrics:
            - Revenue: $2.5M (up 15%)
            - Operating Expenses: $1.8M (down 8%)
            - Net Profit: $362.5K (up 25%)
            """,
            metadata={"document_type": "financial_report", "year": "2024", "section": "summary"}
        ),
        Document(
            page_content="""
            Company Policies and Procedures
            
            All employees must follow the company's code of conduct.
            Remote work is allowed up to 3 days per week.
            Vacation requests must be submitted at least 2 weeks in advance.
            
            The company provides health insurance, dental coverage, and retirement benefits.
            Performance reviews are conducted annually in December.
            """,
            metadata={"document_type": "policy", "category": "hr", "version": "2.1"}
        ),
        Document(
            page_content="""
            Technical Documentation
            
            The API endpoints are documented in the OpenAPI specification.
            Authentication is handled using JWT tokens.
            Rate limiting is set to 1000 requests per hour per user.
            
            Database schema includes users, transactions, and audit logs.
            The system uses PostgreSQL with Redis for caching.
            """,
            metadata={"document_type": "technical", "category": "api", "version": "1.0"}
        ),
        Document(
            page_content="""
            Marketing Strategy
            
            Our target market includes small to medium businesses.
            We focus on digital marketing channels including social media and email.
            Customer acquisition cost has decreased by 20% this quarter.
            
            Key performance indicators:
            - Website traffic: 50K monthly visitors
            - Conversion rate: 3.2%
            - Customer lifetime value: $2,400
            """,
            metadata={"document_type": "marketing", "quarter": "Q3", "department": "marketing"}
        ),
        Document(
            page_content="""
            Legal Compliance
            
            The company is compliant with GDPR regulations.
            Data retention policy requires keeping records for 7 years.
            All contracts must be reviewed by legal department.
            
            Privacy policy was updated in January 2024.
            Terms of service are available on the company website.
            """,
            metadata={"document_type": "legal", "category": "compliance", "last_updated": "2024-01-15"}
        )
    ]
    return documents


def test_relevance_filtering():
    """Test relevance filtering pruning method."""
    print("=" * 60)
    print("Testing Relevance Filtering")
    print("=" * 60)
    
    documents = create_sample_documents()
    query = "financial performance and revenue"
    
    # Test with different configurations
    configs = [
        {"method": "relevance_filter", "similarity_threshold": 0.8, "top_k": None},
        {"method": "relevance_filter", "similarity_threshold": 0.6, "top_k": None},
        {"method": "relevance_filter", "similarity_threshold": 0.7, "top_k": 3},
    ]
    
    for config in configs:
        print(f"\nConfiguration: {config}")
        service = get_context_pruning_service(**config)
        result = service.prune_context(documents, query, **config)
        
        print(f"Original documents: {result.original_count}")
        print(f"Pruned documents: {result.pruned_count}")
        print(f"Compression ratio: {result.compression_ratio:.2f}")
        print(f"Processing time: {result.processing_time:.3f}s")
        print(f"Efficiency: {(1 - result.compression_ratio) * 100:.1f}% reduction")
        
        print("\nPruned documents:")
        for i, doc in enumerate(result.pruned_documents):
            print(f"  {i+1}. {doc.metadata.get('document_type', 'unknown')} - {doc.page_content[:100]}...")


def test_metadata_filtering():
    """Test metadata filtering pruning method."""
    print("\n" + "=" * 60)
    print("Testing Metadata Filtering")
    print("=" * 60)
    
    documents = create_sample_documents()
    query = "financial information"
    
    # Test with different metadata filters
    configs = [
        {"method": "metadata_filter", "metadata_filters": {"document_type": "financial_report"}},
        {"method": "metadata_filter", "metadata_filters": {"category": "hr"}},
        {"method": "metadata_filter", "metadata_filters": {"document_type": "technical"}},
    ]
    
    for config in configs:
        print(f"\nConfiguration: {config}")
        service = get_context_pruning_service(**config)
        result = service.prune_context(documents, query, **config)
        
        print(f"Original documents: {result.original_count}")
        print(f"Pruned documents: {result.pruned_count}")
        print(f"Compression ratio: {result.compression_ratio:.2f}")
        print(f"Processing time: {result.processing_time:.3f}s")
        
        print("\nPruned documents:")
        for i, doc in enumerate(result.pruned_documents):
            print(f"  {i+1}. {doc.metadata.get('document_type', 'unknown')} - {doc.page_content[:100]}...")


def test_hybrid_pruning():
    """Test hybrid pruning method."""
    print("\n" + "=" * 60)
    print("Testing Hybrid Pruning")
    print("=" * 60)
    
    documents = create_sample_documents()
    query = "company policies and financial performance"
    
    # Test hybrid configuration
    config = {
        "method": "hybrid",
        "use_metadata_filter": True,
        "use_relevance_filter": True,
        "use_llm_compression": False,  # Disable LLM compression for faster testing
        "similarity_threshold": 0.6,
        "top_k": 3
    }
    
    print(f"Configuration: {config}")
    service = get_context_pruning_service(**config)
    result = service.prune_context(documents, query, **config)
    
    print(f"Original documents: {result.original_count}")
    print(f"Pruned documents: {result.pruned_count}")
    print(f"Compression ratio: {result.compression_ratio:.2f}")
    print(f"Processing time: {result.processing_time:.3f}s")
    print(f"Efficiency: {(1 - result.compression_ratio) * 100:.1f}% reduction")
    
    print("\nPruning steps:")
    if 'pruning_steps' in result.metadata:
        for step in result.metadata['pruning_steps']:
            print(f"  - {step['step']}: {step['original_count']} -> {step['pruned_count']} documents")
    
    print("\nFinal pruned documents:")
    for i, doc in enumerate(result.pruned_documents):
        print(f"  {i+1}. {doc.metadata.get('document_type', 'unknown')} - {doc.page_content[:100]}...")


def test_context_aware_chunker():
    """Test the context-aware chunker integration."""
    print("\n" + "=" * 60)
    print("Testing Context-Aware Chunker Integration")
    print("=" * 60)
    
    try:
        from document_processing.chunkers.context_aware_chunker import ContextAwareChunker
        from document_processing.parsers.base_parser import ParsedDocument, ParsedElement
        
        # Create a sample parsed document
        elements = [
            ParsedElement(
                content="Financial Performance Summary",
                element_type="header",
                start_position=0,
                end_position=30
            ),
            ParsedElement(
                content="The company showed strong financial performance this quarter with revenue growth of 15% and improved profit margins.",
                element_type="text",
                start_position=31,
                end_position=150
            ),
            ParsedElement(
                content="Key metrics: Revenue $2.5M, Profit $362.5K, Margin 14.5%",
                element_type="text",
                start_position=151,
                end_position=220
            )
        ]
        
        parsed_doc = ParsedDocument(
            content="Financial Performance Summary\nThe company showed strong financial performance this quarter with revenue growth of 15% and improved profit margins.\nKey metrics: Revenue $2.5M, Profit $362.5K, Margin 14.5%",
            elements=elements,
            metadata={"document_type": "financial_report"}
        )
        
        # Test context-aware chunker
        chunker_config = {
            "chunk_size": 200,
            "chunk_overlap": 50,
            "enable_pruning": True,
            "pruning_method": "relevance_filter",
            "pruning_config": {
                "similarity_threshold": 0.7,
                "top_k": 2
            }
        }
        
        chunker = ContextAwareChunker(**chunker_config)
        result = chunker.chunk(parsed_doc)
        
        print(f"Chunking completed:")
        print(f"  Total chunks: {result.total_chunks}")
        print(f"  Processing time: {result.processing_time:.3f}s")
        print(f"  Enable pruning: {result.metadata.get('enable_pruning', False)}")
        print(f"  Pruning method: {result.metadata.get('pruning_method', 'none')}")
        print(f"  Compression ratio: {result.metadata.get('compression_ratio', 1.0):.2f}")
        
        print("\nGenerated chunks:")
        for i, chunk in enumerate(result.chunks):
            print(f"  {i+1}. [{chunk.chunk_type}] {chunk.content[:80]}...")
            print(f"      Tokens: {chunk.token_count}, Metadata: {chunk.metadata}")
        
    except ImportError as e:
        print(f"Context-aware chunker not available: {e}")
    except Exception as e:
        print(f"Error testing context-aware chunker: {e}")


def main():
    """Run all tests."""
    print("Context Pruning Service Test Suite")
    print("=" * 60)
    
    try:
        # Test individual pruning methods
        test_relevance_filtering()
        test_metadata_filtering()
        test_hybrid_pruning()
        
        # Test context-aware chunker integration
        test_context_aware_chunker()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
