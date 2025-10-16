"""
Task Executors for Agentic RAG System.

This module contains specific executors for different types of tasks
that can be planned and executed by the orchestrator.
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .workflow_state import Task, PlannerOrchestratorState

logger = logging.getLogger(__name__)


class BaseTaskExecutor(ABC):
    """Base class for all task executors."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
    
    @abstractmethod
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute a specific task type."""
        pass


class RetrievalTaskExecutor(BaseTaskExecutor):
    """Executor for retrieval tasks - searches and retrieves relevant documents."""
    
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute a retrieval task."""
        try:
            logger.info(f"Executing retrieval task: {task['description']}")
            
            # Extract query from task parameters
            query = task["parameters"].get("query", state["original_query"])
            
            # For now, simulate retrieval - in real implementation, this would use the hybrid retriever
            # TODO: Integrate with actual hybrid retriever when available
            retrieved_docs = self._simulate_retrieval(query)
            
            result = {
                "query_used": query,
                "documents_retrieved": len(retrieved_docs),
                "documents": retrieved_docs,
                "retrieval_method": "simulated_hybrid",
                "confidence": 0.8
            }
            
            logger.info(f"Retrieval completed: {len(retrieved_docs)} documents found")
            return result
            
        except Exception as e:
            logger.error(f"Retrieval task failed: {str(e)}")
            return {
                "error": str(e),
                "documents_retrieved": 0,
                "confidence": 0.0
            }
    
    def _simulate_retrieval(self, query: str) -> List[Dict[str, Any]]:
        """Simulate document retrieval for testing purposes."""
        # This is a placeholder - in real implementation, integrate with hybrid retriever
        return [
            {
                "content": f"Sample document content related to: {query}",
                "source": "sample_document.pdf",
                "relevance_score": 0.9,
                "metadata": {"page": 1, "section": "Introduction"}
            },
            {
                "content": f"Additional information about: {query}",
                "source": "company_policies.txt",
                "relevance_score": 0.7,
                "metadata": {"section": "Policies"}
            }
        ]


class AnalysisTaskExecutor(BaseTaskExecutor):
    """Executor for analysis tasks - analyzes retrieved content for specific information."""
    
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute an analysis task."""
        try:
            logger.info(f"Executing analysis task: {task['description']}")
            
            # Get documents from previous retrieval tasks
            documents = self._get_documents_from_completed_tasks(state)
            
            if not documents:
                return {
                    "error": "No documents available for analysis",
                    "analysis_result": None,
                    "confidence": 0.0
                }
            
            # Perform analysis using LLM
            analysis_result = self._analyze_documents(documents, task, state)
            
            result = {
                "documents_analyzed": len(documents),
                "analysis_result": analysis_result,
                "confidence": 0.8,
                "key_findings": analysis_result.get("key_findings", [])
            }
            
            logger.info(f"Analysis completed: {len(analysis_result.get('key_findings', []))} key findings")
            return result
            
        except Exception as e:
            logger.error(f"Analysis task failed: {str(e)}")
            return {
                "error": str(e),
                "analysis_result": None,
                "confidence": 0.0
            }
    
    def _get_documents_from_completed_tasks(self, state: PlannerOrchestratorState) -> List[Dict[str, Any]]:
        """Extract documents from completed retrieval tasks."""
        documents = []
        for task in state["subtasks"]:
            if (task["task_type"] == "retrieval" and 
                task["status"] == "completed" and 
                task.get("result", {}).get("documents")):
                documents.extend(task["result"]["documents"])
        return documents
    
    def _analyze_documents(
        self, 
        documents: List[Dict[str, Any]], 
        task: Task, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """Analyze documents using LLM."""
        
        # Prepare document content
        doc_content = []
        for i, doc in enumerate(documents[:5]):  # Limit to first 5 docs
            doc_content.append(f"Document {i+1} ({doc.get('source', 'Unknown')}):\n{doc.get('content', '')}\n")
        
        analysis_prompt = f"""Please analyze the following documents to answer the specific question: {task['description']}

Original Query: {state['original_query']}

Documents:
{''.join(doc_content)}

Provide your analysis in JSON format:
{{
    "key_findings": ["finding1", "finding2", ...],
    "relevant_information": "Summary of relevant information",
    "confidence": 0.0-1.0,
    "sources_cited": ["source1", "source2", ...]
}}"""

        messages = [
            SystemMessage(content="You are an expert document analyst. Analyze the provided documents thoroughly and extract relevant information."),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "key_findings": [response.content],
                "relevant_information": response.content,
                "confidence": 0.7,
                "sources_cited": [doc.get("source", "Unknown") for doc in documents]
            }


class SynthesisTaskExecutor(BaseTaskExecutor):
    """Executor for synthesis tasks - combines information from multiple sources."""
    
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute a synthesis task."""
        try:
            logger.info(f"Executing synthesis task: {task['description']}")
            
            # Get information from completed analysis tasks
            analysis_results = self._get_analysis_results(state)
            
            if not analysis_results:
                return {
                    "error": "No analysis results available for synthesis",
                    "synthesis_result": None,
                    "confidence": 0.0
                }
            
            # Perform synthesis using LLM
            synthesis_result = self._synthesize_information(analysis_results, task, state)
            
            result = {
                "sources_synthesized": len(analysis_results),
                "synthesis_result": synthesis_result,
                "confidence": 0.8
            }
            
            logger.info("Synthesis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Synthesis task failed: {str(e)}")
            return {
                "error": str(e),
                "synthesis_result": None,
                "confidence": 0.0
            }
    
    def _get_analysis_results(self, state: PlannerOrchestratorState) -> List[Dict[str, Any]]:
        """Extract analysis results from completed analysis tasks."""
        results = []
        for task in state["subtasks"]:
            if (task["task_type"] == "analysis" and 
                task["status"] == "completed" and 
                task.get("result", {}).get("analysis_result")):
                results.append(task["result"]["analysis_result"])
        return results
    
    def _synthesize_information(
        self, 
        analysis_results: List[Dict[str, Any]], 
        task: Task, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """Synthesize information from multiple analysis results."""
        
        # Prepare analysis data
        analysis_data = []
        for i, result in enumerate(analysis_results):
            analysis_data.append(f"Analysis {i+1}:\n{result.get('relevant_information', '')}\nKey Findings: {result.get('key_findings', [])}\n")
        
        synthesis_prompt = f"""Please synthesize the following analysis results to create a comprehensive understanding of: {task['description']}

Original Query: {state['original_query']}

Analysis Results:
{''.join(analysis_data)}

Provide your synthesis in JSON format:
{{
    "synthesized_information": "Comprehensive synthesis of all information",
    "key_insights": ["insight1", "insight2", ...],
    "confidence": 0.0-1.0,
    "supporting_evidence": ["evidence1", "evidence2", ...]
}}"""

        messages = [
            SystemMessage(content="You are an expert at synthesizing information from multiple sources. Create a comprehensive and coherent synthesis."),
            HumanMessage(content=synthesis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "synthesized_information": response.content,
                "key_insights": [response.content],
                "confidence": 0.7,
                "supporting_evidence": []
            }


class VerificationTaskExecutor(BaseTaskExecutor):
    """Executor for verification tasks - verifies facts and cross-checks information."""
    
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute a verification task."""
        try:
            logger.info(f"Executing verification task: {task['description']}")
            
            # Get information to verify from previous tasks
            information_to_verify = self._get_information_to_verify(state)
            
            if not information_to_verify:
                return {
                    "error": "No information available for verification",
                    "verification_result": None,
                    "confidence": 0.0
                }
            
            # Perform verification
            verification_result = self._verify_information(information_to_verify, task, state)
            
            result = {
                "information_verified": len(information_to_verify),
                "verification_result": verification_result,
                "confidence": 0.8
            }
            
            logger.info("Verification completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Verification task failed: {str(e)}")
            return {
                "error": str(e),
                "verification_result": None,
                "confidence": 0.0
            }
    
    def _get_information_to_verify(self, state: PlannerOrchestratorState) -> List[Dict[str, Any]]:
        """Extract information that needs verification from previous tasks."""
        information = []
        for task in state["subtasks"]:
            if task["status"] == "completed" and task.get("result"):
                information.append({
                    "task_type": task["task_type"],
                    "description": task["description"],
                    "result": task["result"]
                })
        return information
    
    def _verify_information(
        self, 
        information: List[Dict[str, Any]], 
        task: Task, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """Verify information using LLM."""
        
        # Prepare information for verification
        info_content = []
        for i, info in enumerate(information):
            info_content.append(f"Information {i+1} ({info['task_type']}):\n{info['description']}\nResult: {info['result']}\n")
        
        verification_prompt = f"""Please verify the accuracy and consistency of the following information related to: {task['description']}

Original Query: {state['original_query']}

Information to Verify:
{''.join(info_content)}

Provide your verification in JSON format:
{{
    "verification_summary": "Summary of verification findings",
    "accuracy_assessment": "high|medium|low",
    "consistency_check": "consistent|inconsistent|partially_consistent",
    "confidence": 0.0-1.0,
    "issues_found": ["issue1", "issue2", ...],
    "recommendations": ["recommendation1", "recommendation2", ...]
}}"""

        messages = [
            SystemMessage(content="You are an expert at verifying information accuracy and consistency. Provide thorough verification analysis."),
            HumanMessage(content=verification_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "verification_summary": response.content,
                "accuracy_assessment": "medium",
                "consistency_check": "consistent",
                "confidence": 0.7,
                "issues_found": [],
                "recommendations": []
            }


class CalculationTaskExecutor(BaseTaskExecutor):
    """Executor for calculation tasks - performs numerical calculations."""
    
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute a calculation task."""
        try:
            logger.info(f"Executing calculation task: {task['description']}")
            
            # Extract calculation parameters
            calculation_params = task["parameters"]
            
            # Perform calculation (simplified - in real implementation, this could be more sophisticated)
            calculation_result = self._perform_calculation(calculation_params, task, state)
            
            result = {
                "calculation_type": calculation_params.get("type", "unknown"),
                "calculation_result": calculation_result,
                "confidence": 0.9
            }
            
            logger.info("Calculation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Calculation task failed: {str(e)}")
            return {
                "error": str(e),
                "calculation_result": None,
                "confidence": 0.0
            }
    
    def _perform_calculation(
        self, 
        params: Dict[str, Any], 
        task: Task, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """Perform the actual calculation."""
        # This is a simplified implementation
        # In a real system, this could involve complex mathematical operations
        
        calculation_type = params.get("type", "basic")
        
        if calculation_type == "basic":
            return {
                "result": "Calculation completed (simplified implementation)",
                "method": "basic_calculation",
                "details": params
            }
        else:
            return {
                "result": f"Advanced calculation for type: {calculation_type}",
                "method": "advanced_calculation",
                "details": params
            }


class FormattingTaskExecutor(BaseTaskExecutor):
    """Executor for formatting tasks - formats and structures the response."""
    
    def execute(self, task: Task, state: PlannerOrchestratorState) -> Dict[str, Any]:
        """Execute a formatting task."""
        try:
            logger.info(f"Executing formatting task: {task['description']}")
            
            # Get information to format from previous tasks
            content_to_format = self._get_content_to_format(state)
            
            if not content_to_format:
                return {
                    "error": "No content available for formatting",
                    "formatted_result": None,
                    "confidence": 0.0
                }
            
            # Perform formatting
            formatted_result = self._format_content(content_to_format, task, state)
            
            result = {
                "format_type": task["parameters"].get("format", "standard"),
                "formatted_result": formatted_result,
                "confidence": 0.8
            }
            
            logger.info("Formatting completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Formatting task failed: {str(e)}")
            return {
                "error": str(e),
                "formatted_result": None,
                "confidence": 0.0
            }
    
    def _get_content_to_format(self, state: PlannerOrchestratorState) -> List[Dict[str, Any]]:
        """Extract content that needs formatting from previous tasks."""
        content = []
        for task in state["subtasks"]:
            if task["status"] == "completed" and task.get("result"):
                content.append({
                    "task_type": task["task_type"],
                    "content": task["result"]
                })
        return content
    
    def _format_content(
        self, 
        content: List[Dict[str, Any]], 
        task: Task, 
        state: PlannerOrchestratorState
    ) -> Dict[str, Any]:
        """Format content using LLM."""
        
        # Prepare content for formatting
        content_text = []
        for i, item in enumerate(content):
            content_text.append(f"Content {i+1} ({item['task_type']}):\n{item['content']}\n")
        
        format_type = task["parameters"].get("format", "standard")
        
        formatting_prompt = f"""Please format the following content according to the specified format: {format_type}

Original Query: {state['original_query']}

Content to Format:
{''.join(content_text)}

Format Requirements: {task['description']}

Provide the formatted result in JSON format:
{{
    "formatted_content": "The formatted content",
    "format_applied": "{format_type}",
    "structure_used": "Description of the structure applied",
    "confidence": 0.0-1.0
}}"""

        messages = [
            SystemMessage(content="You are an expert at formatting content for different purposes. Apply the requested formatting professionally."),
            HumanMessage(content=formatting_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "formatted_content": response.content,
                "format_applied": format_type,
                "structure_used": "default",
                "confidence": 0.7
            }


class TaskExecutorFactory:
    """Factory for creating task executors."""
    
    def __init__(self):
        self.executors = {
            "retrieval": RetrievalTaskExecutor,
            "analysis": AnalysisTaskExecutor,
            "synthesis": SynthesisTaskExecutor,
            "verification": VerificationTaskExecutor,
            "calculation": CalculationTaskExecutor,
            "formatting": FormattingTaskExecutor
        }
    
    def get_executor(self, task_type: str) -> Optional[BaseTaskExecutor]:
        """Get executor for a specific task type."""
        executor_class = self.executors.get(task_type)
        if executor_class:
            return executor_class()
        return None
    
    def get_available_task_types(self) -> List[str]:
        """Get list of available task types."""
        return list(self.executors.keys())
