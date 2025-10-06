"""
Prompts for the Deep Agent Service.

This module contains all the prompts and instructions used by the deep agent system.
"""

# Main deep agent instructions
DEEP_AGENT_INSTRUCTIONS = """You are an expert document analysis and query answering assistant.

Your job is to:
1. Analyze user queries to understand their intent and requirements
2. Search through available documents to find relevant information
3. Generate comprehensive, accurate, and well-structured responses

You have access to tools for:
- Document search and retrieval
- Query analysis and optimization
- Response generation and synthesis

Always provide accurate information based on the retrieved documents and cite your sources when possible."""

# Tool descriptions for better agent understanding
TOOL_DESCRIPTIONS = {
    "document_search": "Search through available documents to find relevant information based on user queries",
    "query_analysis": "Analyze user queries to understand intent, complexity, and optimal retrieval strategy",
    "response_generation": "Generate comprehensive and accurate responses based on retrieved documents and context"
}

# Error messages
ERROR_MESSAGES = {
    "documents_not_processed": "I apologize, but the document processing system is not ready. Please try again later.",
    "no_documents_found": "No relevant documents found for the query.",
    "processing_error": "I apologize, but I encountered an error while processing your query. Please try again.",
    "response_generation_failed": "I processed your query but couldn't generate a proper response."
}

# Response templates
RESPONSE_TEMPLATES = {
    "query_analysis_format": """Query Analysis Results:
- Query Type: {query_type}
- Information Depth: {information_depth}
- Retrieval Strategy: {retrieval_strategy}
- Complexity: {complexity}
- Response Format: {response_format}
- Confidence: {confidence}
- Intent: {intent}
- Word Count: {word_count}
- Has Question Words: {has_question_words}
- Has Technical Terms: {has_technical_terms}""",
    
    "document_result_format": """Document {index} (Score: {score:.3f}):
Source: {source}
Title: {title}
Content: {content}
""",
    
    "error_response_format": "Error {operation}: {error_message}"
}
