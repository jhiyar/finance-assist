"""
Workflow state definition for new Planner-Orchestrator Agentic RAG.

This module defines the state structure used throughout the new LangGraph workflow.
"""

from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.documents import Document


class Task(TypedDict):
    """Individual task structure."""
    task_id: str
    task_type: str  # "retrieval", "analysis", "synthesis", "verification"
    description: str
    priority: int  # 1 = highest, 5 = lowest
    dependencies: List[str]  # task_ids that must complete first
    parameters: Dict[str, Any]
    status: str  # "pending", "in_progress", "completed", "failed"
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class PlannerOrchestratorState(TypedDict):
    """
    State structure for the new Planner-Orchestrator Agentic RAG workflow.
    
    This state is passed between nodes in the LangGraph workflow and contains
    all the information needed for the planner-orchestrator pipeline.
    """
    
    # Input
    original_query: str
    user_context: Optional[str]
    
    # Planning Phase
    planning_reasoning: str
    subtasks: List[Task]
    execution_plan: List[str]  # ordered task_ids
    
    # Orchestration Phase
    current_task_id: Optional[str]
    completed_tasks: List[str]  # task_ids
    failed_tasks: List[str]  # task_ids
    execution_log: List[Dict[str, Any]]
    
    # Results
    final_answer: str
    confidence_score: float
    citations: List[Dict[str, Any]]
    sources_used: List[str]
    execution_summary: str
    
    # Reflection Phase
    reflection_enabled: bool
    reflection_results: List[Dict[str, Any]]
    needs_more_research: bool
    additional_tasks: List[Task]
    iteration_count: int
    max_iterations: int
    
    # Metadata
    processing_timestamp: str
    workflow_version: str
    error_messages: List[str]
    debug_info: Dict[str, Any]
