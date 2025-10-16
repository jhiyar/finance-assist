"""
Planner Agent for Agentic RAG System.

This agent analyzes user queries and creates a structured plan with subtasks
that need to be executed to answer the query effectively.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .workflow_state import Task

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Agent responsible for analyzing queries and creating execution plans.
    
    The planner breaks down complex queries into manageable subtasks and
    determines the optimal execution order based on dependencies.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        # Task types available for planning
        self.available_task_types = {
            "retrieval": "Search and retrieve relevant documents",
            "analysis": "Analyze retrieved content for specific information",
            "synthesis": "Combine information from multiple sources",
            "verification": "Verify facts and cross-check information",
            "calculation": "Perform numerical calculations or comparisons",
            "formatting": "Format and structure the final response"
        }
        
        logger.info(f"PlannerAgent initialized with model: {model_name}")
    
    def create_execution_plan(
        self, 
        query: str, 
        user_context: Optional[str] = None,
        available_documents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create an execution plan for answering the user query.
        
        Args:
            query: User's question or request
            user_context: Additional context about the user's situation
            available_documents: List of available documents for reference
            
        Returns:
            Dictionary containing the execution plan with subtasks and reasoning
        """
        try:
            logger.info(f"Creating execution plan for query: '{query}'")
            
            # Prepare context for planning
            context_info = self._prepare_planning_context(query, user_context, available_documents)
            
            # Generate subtasks using LLM
            planning_result = self._generate_subtasks(query, context_info)
            
            # Create Task objects
            subtasks = []
            for i, task_info in enumerate(planning_result["subtasks"]):
                task = Task(
                    task_id=f"task_{i+1}_{uuid.uuid4().hex[:8]}",
                    task_type=task_info["type"],
                    description=task_info["description"],
                    priority=task_info["priority"],
                    dependencies=task_info.get("dependencies", []),
                    parameters=task_info.get("parameters", {}),
                    status="pending",
                    result=None,
                    error=None
                )
                subtasks.append(task)
            
            # Determine execution order
            execution_plan = self._determine_execution_order(subtasks)
            
            result = {
                "subtasks": subtasks,
                "execution_plan": execution_plan,
                "planning_reasoning": planning_result["reasoning"],
                "estimated_difficulty": planning_result.get("estimated_difficulty", "medium"),
                "estimated_time": planning_result.get("estimated_time", "unknown")
            }
            
            logger.info(f"Created execution plan with {len(subtasks)} subtasks")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create execution plan: {str(e)}")
            # Fallback: create a simple single-task plan
            return self._create_fallback_plan(query)
    
    def _prepare_planning_context(
        self, 
        query: str, 
        user_context: Optional[str], 
        available_documents: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Prepare context information for planning."""
        context_parts = []
        
        if user_context:
            context_parts.append(f"User Context: {user_context}")
        
        if available_documents:
            doc_titles = [doc.get("title", "Unknown") for doc in available_documents[:10]]
            context_parts.append(f"Available Documents: {', '.join(doc_titles)}")
        
        return "\n".join(context_parts) if context_parts else "No additional context provided."
    
    def _generate_subtasks(self, query: str, context_info: str) -> Dict[str, Any]:
        """Generate subtasks using LLM."""
        
        system_prompt = f"""You are an expert planning agent for a document-based question answering system. 
Your job is to analyze user queries and break them down into specific, actionable subtasks.

Available task types:
{self._format_task_types()}

For each subtask, consider:
1. What specific information needs to be retrieved or analyzed?
2. What dependencies exist between tasks?
3. What priority should each task have (1=highest, 5=lowest)?
4. What parameters might be needed for execution?

Return your response as a JSON object with this structure:
{{
    "reasoning": "Your reasoning for the plan",
    "estimated_difficulty": "easy|medium|hard",
    "estimated_time": "brief description",
    "subtasks": [
        {{
            "type": "task_type",
            "description": "Clear description of what needs to be done",
            "priority": 1-5,
            "dependencies": ["task_id_if_any"],
            "parameters": {{"key": "value"}}
        }}
    ]
}}"""

        user_prompt = f"""Query: "{query}"

Context Information:
{context_info}

Please create a detailed execution plan for answering this query. Break it down into specific subtasks that can be executed sequentially or in parallel where appropriate."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        try:
            import json
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using fallback")
            return self._create_fallback_plan_structure(query)
    
    def _format_task_types(self) -> str:
        """Format available task types for the prompt."""
        return "\n".join([f"- {k}: {v}" for k, v in self.available_task_types.items()])
    
    def _determine_execution_order(self, subtasks: List[Task]) -> List[str]:
        """Determine the optimal execution order for subtasks."""
        # Simple topological sort based on dependencies
        ordered_tasks = []
        remaining_tasks = {task["task_id"]: task for task in subtasks}
        
        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                dependencies_met = all(
                    dep in ordered_tasks for dep in task["dependencies"]
                )
                if dependencies_met:
                    ready_tasks.append((task_id, task))
            
            if not ready_tasks:
                # Circular dependency or error - add remaining tasks
                for task_id in remaining_tasks:
                    ordered_tasks.append(task_id)
                break
            
            # Sort ready tasks by priority
            ready_tasks.sort(key=lambda x: x[1]["priority"])
            
            # Add highest priority task
            task_id, _ = ready_tasks[0]
            ordered_tasks.append(task_id)
            del remaining_tasks[task_id]
        
        return ordered_tasks
    
    def _create_fallback_plan(self, query: str) -> Dict[str, Any]:
        """Create a simple fallback plan when planning fails."""
        task = Task(
            task_id=f"fallback_task_{uuid.uuid4().hex[:8]}",
            task_type="retrieval",
            description=f"Retrieve and analyze documents to answer: {query}",
            priority=1,
            dependencies=[],
            parameters={"query": query},
            status="pending",
            result=None,
            error=None
        )
        
        return {
            "subtasks": [task],
            "execution_plan": [task["task_id"]],
            "planning_reasoning": "Created fallback plan due to planning failure",
            "estimated_difficulty": "medium",
            "estimated_time": "unknown"
        }
    
    def _create_fallback_plan_structure(self, query: str) -> Dict[str, Any]:
        """Create fallback structure when JSON parsing fails."""
        return {
            "reasoning": "Created simple plan due to parsing error",
            "estimated_difficulty": "medium",
            "estimated_time": "unknown",
            "subtasks": [
                {
                    "type": "retrieval",
                    "description": f"Search documents for information about: {query}",
                    "priority": 1,
                    "dependencies": [],
                    "parameters": {"query": query}
                }
            ]
        }
    
    def get_task_type_description(self, task_type: str) -> str:
        """Get description for a specific task type."""
        return self.available_task_types.get(task_type, "Unknown task type")
    
    def validate_task(self, task: Task) -> bool:
        """Validate a task structure."""
        required_fields = ["task_id", "task_type", "description", "priority", "status"]
        return all(field in task for field in required_fields)
