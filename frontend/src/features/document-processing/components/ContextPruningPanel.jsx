import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { 
  Scissors, 
  Settings, 
  Play, 
  BarChart3, 
  Clock, 
  FileText,
  AlertCircle,
  CheckCircle,
  Info,
  Eye
} from 'lucide-react';
import ChunkComparisonModal from './ChunkComparisonModal';

const ContextPruningPanel = ({ documents = [], onPruningComplete }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [pruningResult, setPruningResult] = useState(null);
  const [error, setError] = useState(null);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: {
      method: 'hybrid',
      query: '',
      similarity_threshold: 0.7,
      top_k: 10,
      enable_metadata_filter: true,
      enable_relevance_filter: true,
      enable_llm_compression: false,
      model_name: 'gpt-4o-mini',
      temperature: 0.0
    }
  });

  const selectedMethod = watch('method');

  const onSubmit = useCallback(async (data) => {
    if (!documents.length) {
      setError('No documents available for pruning');
      return;
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

      // Prepare config based on selected method
      const config = {
        similarity_threshold: parseFloat(data.similarity_threshold),
        top_k: data.top_k ? parseInt(data.top_k) : null,
        embedding_model: 'all-MiniLM-L6-v2',
        model_name: data.model_name,
        temperature: parseFloat(data.temperature)
      };

      // Add method-specific config
      if (data.method === 'hybrid') {
        config.use_metadata_filter = data.enable_metadata_filter;
        config.use_relevance_filter = data.enable_relevance_filter;
        config.use_llm_compression = data.enable_llm_compression;
      }

      const response = await fetch('/api/document-processing/context-pruning/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          documents: documentsData,
          query: data.query,
          method: data.method,
          config: config
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Context pruning failed');
      }

      const result = await response.json();
      setPruningResult(result);
      onPruningComplete?.(result);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  }, [documents, onPruningComplete]);

  const formatTime = (seconds) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  const getMethodDescription = (method) => {
    const descriptions = {
      'llm_compression': 'Uses LLM to extract only the most relevant parts of documents',
      'relevance_filter': 'Filters documents based on semantic similarity threshold',
      'metadata_filter': 'Filters documents based on metadata attributes',
      'hybrid': 'Combines multiple pruning strategies for optimal results'
    };
    return descriptions[method] || 'Unknown method';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center space-x-3 mb-6">
        <Scissors className="h-6 w-6 text-blue-600" />
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Context Pruning</h3>
          <p className="text-sm text-gray-600">
            Remove irrelevant content to improve retrieval quality
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Method Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Pruning Method
          </label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { value: 'relevance_filter', label: 'Relevance Filter', icon: BarChart3 },
              { value: 'llm_compression', label: 'LLM Compression', icon: Settings },
              { value: 'metadata_filter', label: 'Metadata Filter', icon: FileText },
              { value: 'hybrid', label: 'Hybrid', icon: Scissors }
            ].map(({ value, label, icon: Icon }) => (
              <label
                key={value}
                className={`
                  relative flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors
                  ${selectedMethod === value 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <input
                  {...register('method')}
                  type="radio"
                  value={value}
                  className="sr-only"
                />
                <Icon className="h-5 w-5 text-gray-600" />
                <div>
                  <div className="font-medium text-sm">{label}</div>
                  <div className="text-xs text-gray-500">
                    {getMethodDescription(value)}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Query Input */}
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Query for Context Relevance
          </label>
          <textarea
            {...register('query', { required: 'Query is required for context pruning' })}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter a query to determine document relevance (e.g., 'financial statements', 'company policies')"
          />
        </div>

        {/* Method-specific Configuration */}
        {selectedMethod === 'relevance_filter' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="similarity_threshold" className="block text-sm font-medium text-gray-700 mb-2">
                Similarity Threshold
              </label>
              <input
                {...register('similarity_threshold', { 
                  required: true, 
                  min: 0, 
                  max: 1,
                  valueAsNumber: true 
                })}
                type="number"
                step="0.1"
                min="0"
                max="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label htmlFor="top_k" className="block text-sm font-medium text-gray-700 mb-2">
                Top K Results (optional)
              </label>
              <input
                {...register('top_k', { valueAsNumber: true })}
                type="number"
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Leave empty for threshold filtering"
              />
            </div>
          </div>
        )}

        {selectedMethod === 'llm_compression' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="model_name" className="block text-sm font-medium text-gray-700 mb-2">
                LLM Model
              </label>
              <select
                {...register('model_name')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>
            <div>
              <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 mb-2">
                Temperature
              </label>
              <input
                {...register('temperature', { 
                  required: true, 
                  min: 0, 
                  max: 2,
                  valueAsNumber: true 
                })}
                type="number"
                step="0.1"
                min="0"
                max="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {selectedMethod === 'hybrid' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Hybrid Pipeline Configuration
            </label>
            <div className="space-y-3">
              <label className="flex items-center space-x-3">
                <input
                  {...register('enable_metadata_filter')}
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">Enable metadata filtering (fastest)</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  {...register('enable_relevance_filter')}
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">Enable relevance filtering (medium speed)</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  {...register('enable_llm_compression')}
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">Enable LLM compression (slowest, highest quality)</span>
              </label>
            </div>
          </div>
        )}

        {/* Document Count Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Info className="h-4 w-4" />
            <span>
              {documents.length} chunk{documents.length !== 1 ? 's' : ''} available for pruning
            </span>
          </div>
          {documents.length > 0 && (
            <div className="mt-2 text-xs text-gray-500">
              Chunks from: {[...new Set(documents.map(doc => doc.metadata?.chunking_method).filter(Boolean))].join(', ')}
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        )}

        {/* Process Button */}
        <button
          type="submit"
          disabled={isProcessing || !documents.length}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {isProcessing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Processing...</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              <span>Apply Context Pruning</span>
            </>
          )}
        </button>
      </form>

      {/* Results Display */}
      {pruningResult && (
        <div className="mt-6 border-t pt-6">
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <h4 className="text-lg font-semibold text-gray-900">Pruning Results</h4>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-600">
                {pruningResult.stats.original_count}
              </div>
              <div className="text-sm text-blue-600">Original</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-600">
                {pruningResult.stats.pruned_count}
              </div>
              <div className="text-sm text-green-600">Pruned</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-purple-600">
                {pruningResult.stats.efficiency}
              </div>
              <div className="text-sm text-purple-600">Reduction</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-orange-600">
                {formatTime(pruningResult.stats.processing_time)}
              </div>
              <div className="text-sm text-orange-600">Time</div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-3">
              <strong>Method:</strong> {pruningResult.stats.pruning_method}
            </div>
            <div className="text-sm text-gray-600 mb-3">
              <strong>Compression Ratio:</strong> {pruningResult.stats.compression_ratio.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600 mb-4">
              <strong>Query:</strong> {pruningResult.metadata?.query || 'N/A'}
            </div>
            <button
              onClick={() => setShowComparisonModal(true)}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors flex items-center justify-center space-x-2"
            >
              <Eye className="h-4 w-4" />
              <span>View Chunk Comparison</span>
            </button>
          </div>
        </div>
      )}

      {/* Chunk Comparison Modal */}
      <ChunkComparisonModal
        isOpen={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        pruningResult={pruningResult}
      />
    </div>
  );
};

export default ContextPruningPanel;
