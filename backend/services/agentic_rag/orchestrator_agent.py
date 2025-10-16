"""
Orchestrator Agent for Agentic RAG System.

This agent manages the execution of subtasks created by the planner,
coordinating between different task execution agents and maintaining state.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .workflow_state import Task, PlannerOrchestratorState
from .task_executors import TaskExecutorFactory

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Agent responsible for orchestrating task execution and maintaining workflow state.
    
    The orchestrator manages the execution of subtasks in the correct order,
    handles task dependencies, and coordinates between different execution agents.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.task_executor_factory = TaskExecutorFactory()
        
        logger.info(f"OrchestratorAgent initialized with model: {model_name}")
    
    def execute_plan(
        self, 
        state: PlannerOrchestratorState
    ) -> PlannerOrchestratorState:
        """
        Execute the planned subtasks in the correct order.
        
        Args:
            state: Current workflow state with subtasks and execution plan
            
        Returns:
            Updated state with execution results
        """
        try:
            logger.info(f"Starting execution of {len(state['subtasks'])} subtasks")
            
            # Initialize execution tracking
            state["completed_tasks"] = []
            state["failed_tasks"] = []
            state["execution_log"] = []
            
            # Execute tasks in order
            for task_id in state["execution_plan"]:
                task = self._find_task_by_id(state["subtasks"], task_id)
                if not task:
                    logger.warning(f"Task {task_id} not found in subtasks")
                    continue
                
                # Execute the task
                execution_result = self._execute_single_task(task, state)
                
                # Update state based on result
                if execution_result["success"]:
                    state["completed_tasks"].append(task_id)
                    task["status"] = "completed"
                    task["result"] = execution_result["result"]
                    logger.info(f"Task {task_id} completed successfully")
                else:
                    state["failed_tasks"].append(task_id)
                    task["status"] = "failed"
                    task["error"] = execution_result["error"]
                    logger.error(f"Task {task_id} failed: {execution_result['error']}")
                
                # Log execution
                state["execution_log"].append({
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                    "success": execution_result["success"],
                    "result": execution_result.get("result"),
                    "error": execution_result.get("error")
                })
                
                # Update current task
                state["current_task_id"] = task_id
            
            # Generate final answer
            state = self._generate_final_answer(state)
            
            logger.info(f"Execution completed: {len(state['completed_tasks'])} successful, {len(state['failed_tasks'])} failed")
            
            return state
            
        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}")
            state["error_messages"].append(f"Orchestration failed: {str(e)}")
            return state
    
    def _execute_single_task(
        self, 
        task: Task, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """Execute a single task using the appropriate executor."""
        try:
            logger.info(f"Executing task {task['task_id']}: {task['description']}")
            
            # Get the appropriate task executor
            executor = self.task_executor_factory.get_executor(task["task_type"])
            if not executor:
                return {
                    "success": False,
                    "error": f"No executor found for task type: {task['task_type']}"
                }
            
            # Execute the task
            result = executor.execute(task, state)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_task_by_id(self, subtasks: List[Task], task_id: str) -> Optional[Task]:
        """Find a task by its ID."""
        for task in subtasks:
            if task["task_id"] == task_id:
                return task
        return None
    
    def _generate_final_answer(self, state: PlannerOrchestratorState) -> PlannerOrchestratorState:
        """Generate the final answer based on completed tasks."""
        try:
            logger.info("Generating final answer")
            
            # Collect results from completed tasks
            task_results = []
            for task in state["subtasks"]:
                if task["status"] == "completed" and task["result"]:
                    task_results.append({
                        "task_id": task["task_id"],
                        "task_type": task["task_type"],
                        "description": task["description"],
                        "result": task["result"]
                    })
            
            # Generate answer using LLM
            answer_prompt = self._create_answer_generation_prompt(
                state["original_query"],
                task_results,
                state.get("user_context")
            )
            
            messages = [
                SystemMessage(content=self._get_answer_generation_system_prompt()),
                HumanMessage(content=answer_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the response
            answer_data = self._parse_answer_response(response.content)
            
            # Update state with final answer
            state["final_answer"] = answer_data["answer"]
            state["confidence_score"] = answer_data.get("confidence", 0.8)
            state["citations"] = answer_data.get("citations", [])
            state["sources_used"] = answer_data.get("sources_used", [])
            state["execution_summary"] = self._create_execution_summary(state)
            
            logger.info("Final answer generated successfully")
            
        except Exception as e:
            logger.error(f"Failed to generate final answer: {str(e)}")
            state["final_answer"] = f"I apologize, but I encountered an error while generating the final answer. Error: {str(e)}"
            state["confidence_score"] = 0.0
            state["citations"] = []
            state["sources_used"] = []
            state["execution_summary"] = "Failed to generate execution summary due to error"
        
        return state
    
    def _create_answer_generation_prompt(
        self, 
        query: str, 
        task_results: List[Dict[str, Any]], 
        user_context: Optional[str]
    ) -> str:
        """Create prompt for final answer generation."""
        prompt_parts = [
            f"Original Query: {query}",
            "",
            "Task Execution Results:"
        ]
        
        for result in task_results:
            prompt_parts.append(f"- Task {result['task_id']} ({result['task_type']}): {result['description']}")
            prompt_parts.append(f"  Result: {result['result']}")
            prompt_parts.append("")
        
        if user_context:
            prompt_parts.append(f"User Context: {user_context}")
            prompt_parts.append("")
        
        prompt_parts.append("Please provide a comprehensive, accurate answer based on the task results above. Include citations where appropriate.")
        
        return "\n".join(prompt_parts)
    
    def _get_answer_generation_system_prompt(self) -> str:
        """Get system prompt for answer generation."""
        return """You are an expert assistant that synthesizes information from multiple task results to provide comprehensive answers to user queries.

Your response should be a JSON object with this structure:
{
    "answer": "The comprehensive answer to the user's query",
    "confidence": 0.0-1.0,
    "citations": [
        {
            "text": "Cited text",
            "source": "Source information",
            "task_id": "task_that_provided_this"
        }
    ],
    "sources_used": ["list", "of", "sources"]
}

Guidelines:
- Provide a clear, comprehensive answer based on all available task results
- Be honest about confidence levels
- Include specific citations for key information
- If information is incomplete or contradictory, mention this
- Use the task results as your primary source of information"""
    
    def _parse_answer_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response for answer generation."""
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse answer response as JSON")
            return {
                "answer": response,
                "confidence": 0.7,
                "citations": [],
                "sources_used": []
            }
    
    def _create_execution_summary(self, state: PlannerOrchestratorState) -> str:
        """Create a summary of the execution process."""
        summary_parts = [
            f"Execution Summary:",
            f"- Total tasks planned: {len(state['subtasks'])}",
            f"- Tasks completed successfully: {len(state['completed_tasks'])}",
            f"- Tasks failed: {len(state['failed_tasks'])}"
        ]
        
        if state["completed_tasks"]:
            summary_parts.append("- Completed tasks:")
            for task_id in state["completed_tasks"]:
                task = self._find_task_by_id(state["subtasks"], task_id)
                if task:
                    summary_parts.append(f"  * {task['description']}")
        
        if state["failed_tasks"]:
            summary_parts.append("- Failed tasks:")
            for task_id in state["failed_tasks"]:
                task = self._find_task_by_id(state["subtasks"], task_id)
                if task:
                    summary_parts.append(f"  * {task['description']}: {task.get('error', 'Unknown error')}")
        
        return "\n".join(summary_parts)
    
    def get_execution_status(self, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Get current execution status."""
        total_tasks = len(state["subtasks"])
        completed = len(state["completed_tasks"])
        failed = len(state["failed_tasks"])
        remaining = total_tasks - completed - failed
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "remaining": remaining,
            "progress_percentage": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            "current_task": state.get("current_task_id"),
            "is_complete": remaining == 0
        }
