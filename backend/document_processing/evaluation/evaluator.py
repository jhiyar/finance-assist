import time
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from ..chunkers.base_chunker import Chunk, ChunkingResult
from ..models import EvaluationMetric

logger = logging.getLogger(__name__)


class ChunkEvaluator:
    """Evaluates chunking results and calculates various metrics."""
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def evaluate_chunking_result(self, chunking_result: ChunkingResult) -> List[EvaluationMetric]:
        """Evaluate a chunking result and return metrics."""
        metrics = []
        
        # Calculate chunk size distribution
        size_dist_metric = self._calculate_chunk_size_distribution(chunking_result)
        metrics.append(size_dist_metric)
        
        # Calculate overlap analysis
        overlap_metric = self._calculate_overlap_analysis(chunking_result)
        metrics.append(overlap_metric)
        
        # Calculate context preservation score
        context_metric = self._calculate_context_preservation(chunking_result)
        metrics.append(context_metric)
        
        # Calculate structure retention rate
        structure_metric = self._calculate_structure_retention(chunking_result)
        metrics.append(structure_metric)
        
        # Calculate semantic coherence score
        semantic_metric = self._calculate_semantic_coherence(chunking_result)
        metrics.append(semantic_metric)
        
        # Calculate processing efficiency
        efficiency_metric = self._calculate_processing_efficiency(chunking_result)
        metrics.append(efficiency_metric)
        
        # Calculate table detection rate (if applicable)
        table_metric = self._calculate_table_detection_rate(chunking_result)
        if table_metric:
            metrics.append(table_metric)
        
        # Calculate hierarchical preservation (if applicable)
        hierarchical_metric = self._calculate_hierarchical_preservation(chunking_result)
        if hierarchical_metric:
            metrics.append(hierarchical_metric)
        
        return metrics
    
    def _calculate_chunk_size_distribution(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate chunk size distribution metrics."""
        chunks = chunking_result.chunks
        
        if not chunks:
            return EvaluationMetric(
                chunking_result=None,  # Will be set when saving
                metric_type='chunk_size_distribution',
                metric_value=0.0,
                metric_details={'error': 'No chunks to evaluate'}
            )
        
        token_counts = [chunk.token_count for chunk in chunks]
        
        details = {
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'mean_tokens': np.mean(token_counts),
            'median_tokens': np.median(token_counts),
            'std_tokens': np.std(token_counts),
            'total_chunks': len(chunks),
            'size_variance': np.var(token_counts)
        }
        
        # Calculate coefficient of variation (lower is better for consistency)
        cv = details['std_tokens'] / details['mean_tokens'] if details['mean_tokens'] > 0 else 0
        details['coefficient_of_variation'] = cv
        
        # Score based on consistency (lower CV is better)
        score = max(0, 1 - cv)
        
        return EvaluationMetric(
            chunking_result=None,  # Will be set when saving
            metric_type='chunk_size_distribution',
            metric_value=score,
            metric_details=details
        )
    
    def _calculate_overlap_analysis(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate overlap analysis metrics."""
        chunks = chunking_result.chunks
        
        if len(chunks) < 2:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='overlap_analysis',
                metric_value=1.0,
                metric_details={'error': 'Insufficient chunks for overlap analysis'}
            )
        
        overlaps = []
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # Calculate positional overlap
            if prev_chunk.end_position > curr_chunk.start_position:
                overlap_size = prev_chunk.end_position - curr_chunk.start_position
                overlap_ratio = overlap_size / min(
                    prev_chunk.end_position - prev_chunk.start_position,
                    curr_chunk.end_position - curr_chunk.start_position
                )
                overlaps.append(overlap_ratio)
        
        if not overlaps:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='overlap_analysis',
                metric_value=0.0,
                metric_details={'error': 'No overlaps detected'}
            )
        
        details = {
            'mean_overlap': np.mean(overlaps),
            'max_overlap': max(overlaps),
            'min_overlap': min(overlaps),
            'overlap_count': len(overlaps),
            'total_pairs': len(chunks) - 1
        }
        
        # Score based on optimal overlap (around 0.1-0.2 is good)
        optimal_overlap = 0.15
        overlap_score = 1 - abs(details['mean_overlap'] - optimal_overlap) / optimal_overlap
        overlap_score = max(0, min(1, overlap_score))
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='overlap_analysis',
            metric_value=overlap_score,
            metric_details=details
        )
    
    def _calculate_context_preservation(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate context preservation score."""
        chunks = chunking_result.chunks
        
        if not chunks:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='context_preservation',
                metric_value=0.0,
                metric_details={'error': 'No chunks to evaluate'}
            )
        
        # Check for parent-child relationships
        chunks_with_parents = sum(1 for chunk in chunks if chunk.parent_chunk is not None)
        chunks_with_children = sum(1 for chunk in chunks if chunk.child_chunks)
        
        # Check for hierarchical metadata
        hierarchical_chunks = sum(1 for chunk in chunks 
                                if 'hierarchical_level' in chunk.metadata)
        
        details = {
            'total_chunks': len(chunks),
            'chunks_with_parents': chunks_with_parents,
            'chunks_with_children': chunks_with_children,
            'hierarchical_chunks': hierarchical_chunks,
            'parent_child_ratio': chunks_with_parents / len(chunks) if chunks else 0,
            'hierarchical_ratio': hierarchical_chunks / len(chunks) if chunks else 0
        }
        
        # Score based on hierarchical preservation
        score = (details['parent_child_ratio'] + details['hierarchical_ratio']) / 2
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='context_preservation',
            metric_value=score,
            metric_details=details
        )
    
    def _calculate_structure_retention(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate structure retention rate."""
        chunks = chunking_result.chunks
        
        if not chunks:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='structure_retention',
                metric_value=0.0,
                metric_details={'error': 'No chunks to evaluate'}
            )
        
        # Count different element types
        type_counts = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        
        # Check for structure-aware metadata
        structure_aware_chunks = sum(1 for chunk in chunks 
                                   if any(key in chunk.metadata for key in 
                                         ['element_type', 'hierarchical_level', 'section_type']))
        
        details = {
            'total_chunks': len(chunks),
            'unique_types': len(type_counts),
            'type_distribution': type_counts,
            'structure_aware_chunks': structure_aware_chunks,
            'structure_awareness_ratio': structure_aware_chunks / len(chunks) if chunks else 0
        }
        
        # Score based on type diversity and structure awareness
        type_diversity_score = min(1.0, details['unique_types'] / 5)  # Normalize to 5 types
        structure_awareness_score = details['structure_awareness_ratio']
        
        score = (type_diversity_score + structure_awareness_score) / 2
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='structure_retention',
            metric_value=score,
            metric_details=details
        )
    
    def _calculate_semantic_coherence(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate semantic coherence score."""
        chunks = chunking_result.chunks
        
        if len(chunks) < 2:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='semantic_coherence',
                metric_value=1.0,
                metric_details={'error': 'Insufficient chunks for semantic analysis'}
            )
        
        # Simple coherence based on content similarity
        # This is a simplified version - in practice, you'd use embeddings
        similarities = []
        
        for i in range(1, len(chunks)):
            prev_content = chunks[i-1].content.lower()
            curr_content = chunks[i].content.lower()
            
            # Simple word overlap similarity
            prev_words = set(prev_content.split())
            curr_words = set(curr_content.split())
            
            if prev_words and curr_words:
                overlap = len(prev_words.intersection(curr_words))
                union = len(prev_words.union(curr_words))
                similarity = overlap / union if union > 0 else 0
                similarities.append(similarity)
        
        if not similarities:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='semantic_coherence',
                metric_value=0.0,
                metric_details={'error': 'Could not calculate similarities'}
            )
        
        details = {
            'mean_similarity': np.mean(similarities),
            'min_similarity': min(similarities),
            'max_similarity': max(similarities),
            'similarity_count': len(similarities)
        }
        
        # Score based on average similarity (higher is better for coherence)
        score = details['mean_similarity']
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='semantic_coherence',
            metric_value=score,
            metric_details=details
        )
    
    def _calculate_processing_efficiency(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate processing efficiency metrics."""
        chunks = chunking_result.chunks
        processing_time = chunking_result.processing_time
        
        if not chunks or processing_time <= 0:
            return EvaluationMetric(
                chunking_result=None,
                metric_type='processing_efficiency',
                metric_value=0.0,
                metric_details={'error': 'Invalid processing data'}
            )
        
        # Calculate efficiency metrics
        chunks_per_second = len(chunks) / processing_time
        total_tokens = sum(chunk.token_count for chunk in chunks)
        tokens_per_second = total_tokens / processing_time if processing_time > 0 else 0
        
        details = {
            'processing_time': processing_time,
            'total_chunks': len(chunks),
            'total_tokens': total_tokens,
            'chunks_per_second': chunks_per_second,
            'tokens_per_second': tokens_per_second
        }
        
        # Score based on processing speed (higher is better)
        # Normalize to a reasonable range (e.g., 100 chunks/second = 1.0)
        score = min(1.0, chunks_per_second / 100)
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='processing_efficiency',
            metric_value=score,
            metric_details=details
        )
    
    def _calculate_table_detection_rate(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate table detection rate."""
        chunks = chunking_result.chunks
        
        if not chunks:
            return None
        
        table_chunks = [chunk for chunk in chunks if chunk.chunk_type == 'table']
        
        details = {
            'total_chunks': len(chunks),
            'table_chunks': len(table_chunks),
            'table_detection_rate': len(table_chunks) / len(chunks) if chunks else 0
        }
        
        # Score based on table detection (presence of tables is good)
        score = details['table_detection_rate']
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='table_detection',
            metric_value=score,
            metric_details=details
        )
    
    def _calculate_hierarchical_preservation(self, chunking_result: ChunkingResult) -> EvaluationMetric:
        """Calculate hierarchical preservation score."""
        chunks = chunking_result.chunks
        
        if not chunks:
            return None
        
        # Check for hierarchical metadata
        hierarchical_chunks = [chunk for chunk in chunks 
                             if 'hierarchical_level' in chunk.metadata]
        
        # Check for parent-child relationships
        chunks_with_relationships = [chunk for chunk in chunks 
                                   if chunk.parent_chunk is not None or chunk.child_chunks]
        
        details = {
            'total_chunks': len(chunks),
            'hierarchical_chunks': len(hierarchical_chunks),
            'chunks_with_relationships': len(chunks_with_relationships),
            'hierarchical_ratio': len(hierarchical_chunks) / len(chunks) if chunks else 0,
            'relationship_ratio': len(chunks_with_relationships) / len(chunks) if chunks else 0
        }
        
        # Score based on hierarchical preservation
        score = (details['hierarchical_ratio'] + details['relationship_ratio']) / 2
        
        return EvaluationMetric(
            chunking_result=None,
            metric_type='hierarchical_preservation',
            metric_value=score,
            metric_details=details
        )
