"""
Reflection Agent for Agentic RAG System.

This agent evaluates the quality and completeness of execution results
and determines if additional research or tasks are needed.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .workflow_state import Task, PlannerOrchestratorState

logger = logging.getLogger(__name__)


class ReflectionAgent:
    """
    Agent responsible for reflecting on execution results and determining if more research is needed.
    
    The reflection agent evaluates the quality, completeness, and accuracy of the results
    and can suggest additional tasks or iterations if the current answer is insufficient.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        logger.info(f"ReflectionAgent initialized with model: {model_name}")
    
    def reflect_on_execution(
        self, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """
        Reflect on the current execution results and determine if more research is needed.
        
        Args:
            state: Current workflow state with execution results
            
        Returns:
            Dictionary containing reflection results and recommendations
        """
        try:
            logger.info("Starting reflection on execution results")
            
            # Analyze the current results
            reflection_analysis = self._analyze_results(state)
            
            # Determine if more research is needed
            needs_more_research = reflection_analysis["needs_more_research"]
            
            # Generate additional tasks if needed
            additional_tasks = []
            if needs_more_research and state["iteration_count"] < state["max_iterations"]:
                additional_tasks = self._generate_additional_tasks(state, reflection_analysis)
            
            result = {
                "reflection_analysis": reflection_analysis,
                "needs_more_research": needs_more_research,
                "additional_tasks": additional_tasks,
                "confidence_improvement": reflection_analysis.get("confidence_improvement", 0.0),
                "recommendations": reflection_analysis.get("recommendations", []),
                "quality_assessment": reflection_analysis.get("quality_assessment", "unknown")
            }
            
            logger.info(f"Reflection completed: needs_more_research={needs_more_research}, additional_tasks={len(additional_tasks)}")
            return result
            
        except Exception as e:
            logger.error(f"Reflection failed: {str(e)}")
            return {
                "reflection_analysis": {"error": str(e)},
                "needs_more_research": False,
                "additional_tasks": [],
                "confidence_improvement": 0.0,
                "recommendations": ["Reflection failed due to error"],
                "quality_assessment": "error"
            }
    
    def _analyze_results(self, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Analyze the current execution results."""
        
        # Prepare analysis context
        analysis_context = self._prepare_analysis_context(state)
        
        # Use LLM to analyze the results
        analysis_prompt = self._create_analysis_prompt(state, analysis_context)
        
        messages = [
            SystemMessage(content=self._get_analysis_system_prompt()),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse the response
        try:
            import json
            analysis_result = json.loads(response.content)
            return analysis_result
        except json.JSONDecodeError:
            logger.warning("Failed to parse reflection analysis as JSON")
            return self._create_fallback_analysis(state)
    
    def _prepare_analysis_context(self, state: PlannerOrchestratorState) -> str:
        """Prepare context for analysis."""
        context_parts = []
        
        # Execution summary
        context_parts.append("EXECUTION SUMMARY:")
        context_parts.append(f"- Total tasks planned: {len(state['subtasks'])}")
        context_parts.append(f"- Tasks completed: {len(state['completed_tasks'])}")
        context_parts.append(f"- Tasks failed: {len(state['failed_tasks'])}")
        context_parts.append(f"- Current iteration: {state['iteration_count']}")
        context_parts.append("")
        
        # Task results
        context_parts.append("TASK RESULTS:")
        for task in state["subtasks"]:
            if task["status"] == "completed":
                context_parts.append(f"✓ {task['task_type']}: {task['description']}")
                if task.get("result"):
                    result_summary = str(task["result"])[:200] + "..." if len(str(task["result"])) > 200 else str(task["result"])
                    context_parts.append(f"  Result: {result_summary}")
            elif task["status"] == "failed":
                context_parts.append(f"❌ {task['task_type']}: {task['description']}")
                if task.get("error"):
                    context_parts.append(f"  Error: {task['error']}")
        context_parts.append("")
        
        # Final answer
        context_parts.append("FINAL ANSWER:")
        answer_preview = state.get("final_answer", "No answer generated")
        if len(answer_preview) > 300:
            answer_preview = answer_preview[:300] + "..."
        context_parts.append(answer_preview)
        context_parts.append("")
        
        # Confidence and sources
        context_parts.append("QUALITY METRICS:")
        context_parts.append(f"- Confidence Score: {state.get('confidence_score', 0.0):.2f}")
        context_parts.append(f"- Sources Used: {len(state.get('sources_used', []))}")
        context_parts.append(f"- Citations: {len(state.get('citations', []))}")
        context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, state: PlannerOrchestratorState, analysis_context: str) -> str:
        """Create prompt for result analysis."""
        return f"""Please analyze the following execution results for the query: "{state['original_query']}"

{analysis_context}

Evaluate the following aspects:
1. Completeness: Is the answer complete and comprehensive?
2. Accuracy: Are the facts and information accurate?
3. Relevance: Does the answer directly address the user's question?
4. Quality: Is the answer well-structured and clear?
5. Confidence: Is the confidence score appropriate for the quality?

Provide your analysis in JSON format:
{{
    "quality_assessment": "excellent|good|adequate|poor|inadequate",
    "completeness_score": 0.0-1.0,
    "accuracy_score": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "confidence_improvement": 0.0-1.0,
    "needs_more_research": true|false,
    "missing_aspects": ["aspect1", "aspect2", ...],
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "recommendations": ["recommendation1", "recommendation2", ...],
    "reasoning": "Detailed explanation of the analysis"
}}"""
    
    def _get_analysis_system_prompt(self) -> str:
        """Get system prompt for analysis."""
        return """You are an expert quality assessor for AI-generated answers. Your job is to critically evaluate the completeness, accuracy, and quality of answers generated by an agentic RAG system.

Guidelines for assessment:
- Be thorough but fair in your evaluation
- Consider both the content quality and the process quality
- Identify specific areas that need improvement
- Provide actionable recommendations
- Consider the user's original query when evaluating relevance

Be honest about limitations and don't hesitate to recommend additional research if the answer is incomplete or inaccurate."""
    
    def _generate_additional_tasks(
        self, 
        state: PlannerOrchestratorState, 
        analysis: Dict[str, Any]
    ) -> List[Task]:
        """Generate additional tasks based on analysis."""
        additional_tasks = []
        
        try:
            missing_aspects = analysis.get("missing_aspects", [])
            recommendations = analysis.get("recommendations", [])
            
            # Generate tasks for missing aspects
            for i, aspect in enumerate(missing_aspects[:3]):  # Limit to 3 additional tasks
                task = Task(
                    task_id=f"reflection_task_{i+1}_{uuid.uuid4().hex[:8]}",
                    task_type="retrieval",
                    description=f"Research additional information about: {aspect}",
                    priority=2,  # Higher priority than original tasks
                    dependencies=[],
                    parameters={
                        "query": f"{state['original_query']} specifically about {aspect}",
                        "focus_area": aspect
                    },
                    status="pending",
                    result=None,
                    error=None
                )
                additional_tasks.append(task)
            
            # Generate tasks based on recommendations
            for i, recommendation in enumerate(recommendations[:2]):  # Limit to 2 recommendation tasks
                task = Task(
                    task_id=f"recommendation_task_{i+1}_{uuid.uuid4().hex[:8]}",
                    task_type="analysis",
                    description=f"Follow recommendation: {recommendation}",
                    priority=3,
                    dependencies=[],
                    parameters={
                        "recommendation": recommendation,
                        "original_query": state["original_query"]
                    },
                    status="pending",
                    result=None,
                    error=None
                )
                additional_tasks.append(task)
            
            logger.info(f"Generated {len(additional_tasks)} additional tasks based on reflection")
            
        except Exception as e:
            logger.error(f"Failed to generate additional tasks: {str(e)}")
        
        return additional_tasks
    
    def _create_fallback_analysis(self, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Create fallback analysis when JSON parsing fails."""
        confidence = state.get("confidence_score", 0.0)
        
        # Simple heuristic-based analysis
        if confidence >= 0.8:
            quality_assessment = "good"
            needs_more_research = False
        elif confidence >= 0.6:
            quality_assessment = "adequate"
            needs_more_research = len(state.get("sources_used", [])) < 2
        else:
            quality_assessment = "poor"
            needs_more_research = True
        
        return {
            "quality_assessment": quality_assessment,
            "completeness_score": confidence,
            "accuracy_score": confidence,
            "relevance_score": confidence,
            "confidence_improvement": 0.1 if needs_more_research else 0.0,
            "needs_more_research": needs_more_research,
            "missing_aspects": ["additional verification"] if needs_more_research else [],
            "strengths": ["Basic answer provided"],
            "weaknesses": ["Limited confidence"] if needs_more_research else [],
            "recommendations": ["Seek additional sources"] if needs_more_research else [],
            "reasoning": "Fallback analysis based on confidence score"
        }
    
    def should_continue_iteration(self, state: PlannerOrchestratorState) -> bool:
        """Determine if the system should continue with another iteration."""
        return (
            state.get("reflection_enabled", False) and
            state.get("needs_more_research", False) and
            state.get("iteration_count", 0) < state.get("max_iterations", 3)
        )
    
    def get_reflection_summary(self, reflection_results: List[Dict[str, Any]]) -> str:
        """Generate a summary of all reflection results."""
        if not reflection_results:
            return "No reflection performed"
        
        summary_parts = []
        summary_parts.append("=== REFLECTION SUMMARY ===")
        summary_parts.append(f"Total iterations: {len(reflection_results)}")
        
        for i, result in enumerate(reflection_results):
            summary_parts.append(f"\nIteration {i+1}:")
            analysis = result.get("reflection_analysis", {})
            summary_parts.append(f"- Quality: {analysis.get('quality_assessment', 'unknown')}")
            summary_parts.append(f"- Needs more research: {result.get('needs_more_research', False)}")
            summary_parts.append(f"- Additional tasks: {len(result.get('additional_tasks', []))}")
            
            if result.get("recommendations"):
                summary_parts.append(f"- Recommendations: {', '.join(result['recommendations'][:3])}")
        
        return "\n".join(summary_parts)
