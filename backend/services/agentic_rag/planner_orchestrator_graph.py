"""
Planner-Orchestrator LangGraph workflow implementation.

This module implements the main LangGraph workflow that orchestrates the
planner and orchestrator agents in the new Agentic RAG pipeline.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

from .workflow_state import PlannerOrchestratorState
from .planner_agent import PlannerAgent
from .orchestrator_agent import OrchestratorAgent
from .reflection_agent import ReflectionAgent

logger = logging.getLogger(__name__)


class PlannerOrchestratorGraph:
    """
    New Planner-Orchestrator workflow implemented as a LangGraph.
    
    This workflow orchestrates the following phases:
    1. Planning Phase: Analyze query and create subtasks
    2. Orchestration Phase: Execute subtasks in order
    3. Finalization Phase: Generate final answer and summary
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        available_documents: Optional[List[Dict[str, Any]]] = None,
        enable_reflection: bool = False,
        max_iterations: int = 3
    ):
        self.model_name = model_name
        self.available_documents = available_documents or []
        self.enable_reflection = enable_reflection
        self.max_iterations = max_iterations
        
        # Initialize agents
        self.planner_agent = PlannerAgent(model_name)
        self.orchestrator_agent = OrchestratorAgent(model_name)
        self.reflection_agent = ReflectionAgent(model_name)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        logger.info(f"PlannerOrchestratorGraph initialized with model: {model_name}, reflection: {enable_reflection}")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(PlannerOrchestratorState)
        
        # Add nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("orchestrator", self._orchestrator_node)
        
        if self.enable_reflection:
            workflow.add_node("reflection", self._reflection_node)
            workflow.add_node("finalizer", self._finalizer_node)
        else:
            workflow.add_node("finalizer", self._finalizer_node)
        
        # Define the workflow edges
        workflow.set_entry_point("planner")
        
        if self.enable_reflection:
            workflow.add_edge("planner", "orchestrator")
            workflow.add_conditional_edges(
                "orchestrator",
                self._should_reflect,
                {
                    "reflect": "reflection",
                    "finalize": "finalizer"
                }
            )
            workflow.add_conditional_edges(
                "reflection",
                self._should_continue_iteration,
                {
                    "continue": "orchestrator",
                    "finalize": "finalizer"
                }
            )
            workflow.add_edge("finalizer", END)
        else:
            workflow.add_edge("planner", "orchestrator")
            workflow.add_edge("orchestrator", "finalizer")
            workflow.add_edge("finalizer", END)
        
        # Compile the workflow
        return workflow.compile()
    
    def _planner_node(self, state: PlannerOrchestratorState) -> PlannerOrchestratorState:
        """Planning phase node."""
        try:
            logger.info("Starting planning phase")
            
            # Create execution plan using planner agent
            planning_result = self.planner_agent.create_execution_plan(
                query=state["original_query"],
                user_context=state.get("user_context"),
                available_documents=self.available_documents
            )
            
            # Update state with planning results
            state["subtasks"] = planning_result["subtasks"]
            state["execution_plan"] = planning_result["execution_plan"]
            state["planning_reasoning"] = planning_result["planning_reasoning"]
            
            logger.info(f"Planning completed: {len(state['subtasks'])} subtasks created")
            
        except Exception as e:
            error_msg = f"Planning phase failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: create a simple single-task plan
            from .workflow_state import Task
            import uuid
            
            fallback_task = Task(
                task_id=f"fallback_task_{uuid.uuid4().hex[:8]}",
                task_type="retrieval",
                description=f"Retrieve information to answer: {state['original_query']}",
                priority=1,
                dependencies=[],
                parameters={"query": state["original_query"]},
                status="pending",
                result=None,
                error=None
            )
            
            state["subtasks"] = [fallback_task]
            state["execution_plan"] = [fallback_task["task_id"]]
            state["planning_reasoning"] = "Fallback plan created due to planning failure"
        
        return state
    
    def _orchestrator_node(self, state: PlannerOrchestratorState) -> PlannerOrchestratorState:
        """Orchestration phase node."""
        try:
            logger.info("Starting orchestration phase")
            
            # Execute the plan using orchestrator agent
            state = self.orchestrator_agent.execute_plan(state)
            
            logger.info("Orchestration phase completed")
            
        except Exception as e:
            error_msg = f"Orchestration phase failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Set fallback values
            state["final_answer"] = f"I apologize, but I encountered an error while processing your query: '{state['original_query']}'. Please try again."
            state["confidence_score"] = 0.0
            state["citations"] = []
            state["sources_used"] = []
            state["execution_summary"] = "Execution failed due to orchestration error"
        
        return state
    
    def _reflection_node(self, state: PlannerOrchestratorState) -> PlannerOrchestratorState:
        """Reflection phase node."""
        try:
            logger.info("Starting reflection phase")
            
            # Perform reflection using reflection agent
            reflection_result = self.reflection_agent.reflect_on_execution(state)
            
            # Update state with reflection results
            state["reflection_results"].append(reflection_result)
            state["needs_more_research"] = reflection_result["needs_more_research"]
            
            # Add additional tasks if needed
            if reflection_result["additional_tasks"]:
                state["additional_tasks"].extend(reflection_result["additional_tasks"])
                # Add new tasks to the execution plan
                new_task_ids = [task["task_id"] for task in reflection_result["additional_tasks"]]
                state["execution_plan"].extend(new_task_ids)
                state["subtasks"].extend(reflection_result["additional_tasks"])
            
            logger.info(f"Reflection completed: needs_more_research={state['needs_more_research']}")
            
        except Exception as e:
            error_msg = f"Reflection phase failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Set fallback values
            state["needs_more_research"] = False
            state["reflection_results"].append({
                "reflection_analysis": {"error": str(e)},
                "needs_more_research": False,
                "additional_tasks": [],
                "confidence_improvement": 0.0,
                "recommendations": ["Reflection failed due to error"],
                "quality_assessment": "error"
            })
        
        return state
    
    def _should_reflect(self, state: PlannerOrchestratorState) -> str:
        """Determine if reflection should be performed."""
        if not self.enable_reflection:
            return "finalize"
        
        # Check if we've reached max iterations
        if state["iteration_count"] >= state["max_iterations"]:
            logger.info("Max iterations reached, skipping reflection")
            return "finalize"
        
        # Always reflect if reflection is enabled and we haven't reached max iterations
        return "reflect"
    
    def _should_continue_iteration(self, state: PlannerOrchestratorState) -> str:
        """Determine if another iteration should be performed."""
        if not self.enable_reflection:
            return "finalize"
        
        # Check if reflection recommends more research
        if state["needs_more_research"] and state["iteration_count"] < state["max_iterations"]:
            # Increment iteration count
            state["iteration_count"] += 1
            logger.info(f"Starting iteration {state['iteration_count']}")
            return "continue"
        
        logger.info("No more research needed or max iterations reached, finalizing")
        return "finalize"
    
    def _finalizer_node(self, state: PlannerOrchestratorState) -> PlannerOrchestratorState:
        """Finalization phase node."""
        try:
            logger.info("Starting finalization phase")
            
            # Create comprehensive execution report
            execution_report = self._create_execution_report(state)
            state["execution_summary"] = execution_report
            
            # Add final metadata
            state["processing_timestamp"] = datetime.now().isoformat()
            state["workflow_version"] = "2.0"
            
            logger.info("Finalization phase completed")
            
        except Exception as e:
            error_msg = f"Finalization phase failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Set minimal execution summary
            state["execution_summary"] = f"Execution completed with errors: {error_msg}"
        
        return state
    
    def _create_execution_report(self, state: PlannerOrchestratorState) -> str:
        """Create a comprehensive execution report."""
        report_parts = []
        
        # Header
        report_parts.append("=== EXECUTION REPORT ===")
        report_parts.append(f"Query: {state['original_query']}")
        report_parts.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append("")
        
        # Planning Summary
        report_parts.append("PLANNING PHASE:")
        report_parts.append(f"- Total subtasks planned: {len(state['subtasks'])}")
        report_parts.append(f"- Planning reasoning: {state.get('planning_reasoning', 'N/A')}")
        report_parts.append("")
        
        # Task Execution Summary
        report_parts.append("TASK EXECUTION:")
        completed_count = len(state.get('completed_tasks', []))
        failed_count = len(state.get('failed_tasks', []))
        total_count = len(state['subtasks'])
        
        report_parts.append(f"- Total tasks: {total_count}")
        report_parts.append(f"- Completed successfully: {completed_count}")
        report_parts.append(f"- Failed: {failed_count}")
        report_parts.append(f"- Success rate: {(completed_count/total_count*100):.1f}%" if total_count > 0 else "- Success rate: 0%")
        report_parts.append(f"- Iterations performed: {state.get('iteration_count', 1)}")
        report_parts.append("")
        
        # Reflection Summary
        if state.get('reflection_enabled', False):
            report_parts.append("REFLECTION PHASE:")
            reflection_results = state.get('reflection_results', [])
            report_parts.append(f"- Reflection iterations: {len(reflection_results)}")
            report_parts.append(f"- Needs more research: {state.get('needs_more_research', False)}")
            report_parts.append(f"- Additional tasks generated: {len(state.get('additional_tasks', []))}")
            
            if reflection_results:
                for i, result in enumerate(reflection_results):
                    analysis = result.get('reflection_analysis', {})
                    report_parts.append(f"- Iteration {i+1} quality: {analysis.get('quality_assessment', 'unknown')}")
                    if result.get('recommendations'):
                        report_parts.append(f"  Recommendations: {', '.join(result['recommendations'][:2])}")
            report_parts.append("")
        
        # Detailed Task Results
        report_parts.append("DETAILED TASK RESULTS:")
        for task in state['subtasks']:
            status_emoji = "✅" if task['status'] == 'completed' else "❌"
            report_parts.append(f"{status_emoji} {task['task_id']} ({task['task_type']}): {task['description']}")
            if task['status'] == 'failed' and task.get('error'):
                report_parts.append(f"   Error: {task['error']}")
        report_parts.append("")
        
        # Final Answer Summary
        report_parts.append("FINAL ANSWER:")
        report_parts.append(f"- Confidence Score: {state.get('confidence_score', 0.0):.2f}")
        report_parts.append(f"- Sources Used: {len(state.get('sources_used', []))}")
        report_parts.append(f"- Citations: {len(state.get('citations', []))}")
        report_parts.append("")
        
        # Answer Preview (truncated)
        answer_preview = state.get('final_answer', 'No answer generated')
        if len(answer_preview) > 200:
            answer_preview = answer_preview[:200] + "..."
        report_parts.append(f"Answer Preview: {answer_preview}")
        report_parts.append("")
        
        # Error Summary
        if state.get('error_messages'):
            report_parts.append("ERRORS ENCOUNTERED:")
            for error in state['error_messages']:
                report_parts.append(f"- {error}")
            report_parts.append("")
        
        # Footer
        report_parts.append("=== END OF REPORT ===")
        
        return "\n".join(report_parts)
    
    def run_workflow(
        self,
        query: str,
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete Planner-Orchestrator workflow.
        
        Args:
            query: User query
            user_context: Additional user context (optional)
            
        Returns:
            Dictionary with workflow results
        """
        try:
            # Initialize state
            initial_state: PlannerOrchestratorState = {
                "original_query": query,
                "user_context": user_context,
                "planning_reasoning": "",
                "subtasks": [],
                "execution_plan": [],
                "current_task_id": None,
                "completed_tasks": [],
                "failed_tasks": [],
                "execution_log": [],
                "final_answer": "",
                "confidence_score": 0.0,
                "citations": [],
                "sources_used": [],
                "execution_summary": "",
                "reflection_enabled": self.enable_reflection,
                "reflection_results": [],
                "needs_more_research": False,
                "additional_tasks": [],
                "iteration_count": 1,
                "max_iterations": self.max_iterations,
                "processing_timestamp": "",
                "workflow_version": "2.0",
                "error_messages": [],
                "debug_info": {}
            }
            
            # Run the workflow
            logger.info(f"Starting Planner-Orchestrator workflow for query: '{query}'")
            final_state = self.workflow.invoke(initial_state)
            
            # Prepare result (maintaining backward compatibility)
            result = {
                "query": query,
                "answer": final_state["final_answer"],
                "confidence": final_state["confidence_score"],
                "citations": final_state["citations"],
                "sources_used": final_state["sources_used"],
                "execution_summary": final_state["execution_summary"],
                "processing_info": {
                    "subtasks_planned": len(final_state["subtasks"]),
                    "tasks_completed": len(final_state["completed_tasks"]),
                    "tasks_failed": len(final_state["failed_tasks"]),
                    "planning_reasoning": final_state["planning_reasoning"],
                    "execution_log": final_state["execution_log"]
                },
                "execution_log": final_state["execution_log"],
                "errors": final_state["error_messages"],
                "timestamp": final_state["processing_timestamp"],
                "workflow_version": final_state["workflow_version"],
                # Backward compatibility fields
                "reasoning": {
                    "planning": final_state["planning_reasoning"],
                    "execution_summary": final_state["execution_summary"]
                },
                "confidence_scores": {
                    "final_confidence": final_state["confidence_score"],
                    "planning_confidence": 0.8  # Default value for backward compatibility
                }
            }
            
            logger.info("Planner-Orchestrator workflow completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                "query": query,
                "answer": f"I apologize, but I encountered an error while processing your query: '{query}'. Please try again.",
                "confidence": 0.0,
                "citations": [],
                "sources_used": [],
                "execution_summary": f"Workflow failed: {error_msg}",
                "processing_info": {},
                "execution_log": [],
                "errors": [error_msg],
                "timestamp": datetime.now().isoformat(),
                "workflow_version": "2.0",
                # Backward compatibility fields
                "reasoning": {
                    "planning": "Planning failed",
                    "execution_summary": f"Workflow failed: {error_msg}"
                },
                "confidence_scores": {
                    "final_confidence": 0.0,
                    "planning_confidence": 0.0
                }
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow configuration."""
        return {
            "model_name": self.model_name,
            "workflow_version": "2.0",
            "available_documents": len(self.available_documents),
            "phases": ["planner", "orchestrator", "finalizer"],
            "planner_info": {
                "available_task_types": list(self.planner_agent.available_task_types.keys())
            },
            "orchestrator_info": {
                "available_executors": self.orchestrator_agent.task_executor_factory.get_available_task_types()
            }
        }
    
    def get_execution_status(self, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Get current execution status (for monitoring)."""
        return self.orchestrator_agent.get_execution_status(state)
