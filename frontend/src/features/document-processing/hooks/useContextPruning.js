import { useState, useCallback } from 'react';

export const useContextPruning = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [pruningResult, setPruningResult] = useState(null);
  const [error, setError] = useState(null);

  const pruneContext = useCallback(async (documents, query, method = 'hybrid', config = {}) => {
    if (!documents.length) {
      setError('No documents available for pruning');
      return null;
    }

    setIsProcessing(true);
    setError(null);
    setPruningResult(null);

    try {
      // Prepare documents for API
      const documentsData = documents.map(doc => ({
        content: doc.content || doc.page_content || '',
        metadata: doc.metadata || {}
      }));

      const response = await fetch('/api/document-processing/context-pruning/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          documents: documentsData,
          query,
          method,
          config
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Context pruning failed');
      }

      const result = await response.json();
      setPruningResult(result);
      return result;

    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setPruningResult(null);
    setError(null);
  }, []);

  return {
    pruneContext,
    isProcessing,
    pruningResult,
    error,
    clearResults
  };
};
