import React, { useState, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { 
  Scissors, 
  Play, 
  FileText, 
  BarChart3, 
  Clock, 
  CheckCircle,
  AlertCircle,
  Info,
  Eye,
  Copy,
  Download,
  Upload,
  File,
  X
} from 'lucide-react';
import { formatChunkContent } from '../utils/contentUtils';

const ContextPruningTestPage = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [isUploadMode, setIsUploadMode] = useState(false);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const fileInputRef = useRef(null);
  
  const { register, handleSubmit, watch, setValue } = useForm({
    defaultValues: {
      input_text: '',
      query: '',
      methods: ['relevance_filter', 'llm_compression', 'metadata_filter', 'hybrid'],
      similarity_threshold: 0.7,
      top_k: 10,
      model_name: 'gpt-4o-mini',
      temperature: 0.0
    }
  });

  const selectedMethods = watch('methods');

  // File processing functions
  const processFile = async (file) => {
    if (!file) return;
    
    setIsProcessingFile(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/document-processing/parse-document/', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Failed to process file');
      }
      
      const result = await response.json();
      const extractedText = result.content || result.text || '';
      
      setFileContent(extractedText);
      setValue('input_text', extractedText);
      setUploadedFile(file);
      
    } catch (err) {
      setError(`Failed to process file: ${err.message}`);
      setUploadedFile(null);
      setFileContent('');
    } finally {
      setIsProcessingFile(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      processFile(file);
    } else {
      setError('Please upload a PDF file');
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      processFile(file);
    } else {
      setError('Please upload a PDF file');
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const removeFile = () => {
    setUploadedFile(null);
    setFileContent('');
    setValue('input_text', '');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const selectTextMode = () => {
    if (isUploadMode) {
      setIsUploadMode(false);
      // Switching to text mode - clear file
      removeFile();
    }
  };

  const selectUploadMode = () => {
    if (!isUploadMode) {
      setIsUploadMode(true);
      // Switching to upload mode - clear text input
      setValue('input_text', '');
    }
  };

  const onSubmit = async (data) => {
    const inputText = isUploadMode ? fileContent : data.input_text;
    
    if (!inputText.trim()) {
      setError(isUploadMode ? 'Please upload a PDF file' : 'Please enter some text to test');
      return;
    }

    if (!data.query.trim()) {
      setError('Please enter a query for context relevance');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setResults(null);

    try {
      // Create documents from the input text
      const documents = [{
        content: inputText,
        metadata: {
          source: isUploadMode ? uploadedFile?.name || 'uploaded_file' : 'user_input',
          chunking_method: 'manual',
          chunk_type: isUploadMode ? 'pdf' : 'text'
        }
      }];

      // Test each selected method
      const methodResults = {};
      
      for (const method of data.methods) {
        try {
          const config = {
            similarity_threshold: parseFloat(data.similarity_threshold),
            top_k: data.top_k ? parseInt(data.top_k) : null,
            embedding_model: 'all-MiniLM-L6-v2',
            model_name: data.model_name,
            temperature: parseFloat(data.temperature)
          };

          // Add method-specific config
          if (method === 'hybrid') {
            config.use_metadata_filter = true;
            config.use_relevance_filter = true;
            config.use_llm_compression = false; // Disable for faster testing
          }

          const response = await fetch('/api/document-processing/context-pruning/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              documents: documents,
              query: data.query,
              method: method,
              config: config
            })
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `${method} pruning failed`);
          }

          const result = await response.json();
          methodResults[method] = result;

        } catch (methodError) {
          console.error(`Error with method ${method}:`, methodError);
          methodResults[method] = {
            error: methodError.message,
            stats: {
              original_count: 1,
              pruned_count: 0,
              compression_ratio: 0,
              processing_time: 0,
              pruning_method: method,
              efficiency: '0% reduction'
            }
          };
        }
      }

      setResults({
        input_text: inputText,
        query: data.query,
        method_results: methodResults,
        timestamp: new Date().toISOString(),
        source: isUploadMode ? uploadedFile?.name || 'uploaded_file' : 'text_input'
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const exportResults = () => {
    if (!results) return;
    
    const data = {
      input_text: results.input_text,
      query: results.query,
      timestamp: results.timestamp,
      results: results.method_results
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `context-pruning-test-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getMethodDescription = (method) => {
    const descriptions = {
      'llm_compression': 'Uses LLM to extract only the most relevant parts',
      'relevance_filter': 'Filters based on semantic similarity threshold',
      'metadata_filter': 'Filters based on metadata attributes',
      'hybrid': 'Combines multiple pruning strategies'
    };
    return descriptions[method] || 'Unknown method';
  };

  const getMethodIcon = (method) => {
    const icons = {
      'llm_compression': BarChart3,
      'relevance_filter': Scissors,
      'metadata_filter': FileText,
      'hybrid': Play
    };
    return icons[method] || FileText;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Context Pruning Test</h1>
          <p className="mt-2 text-gray-600">
            Test different context pruning methods with your own text and queries
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-6">
              <Scissors className="h-6 w-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">Test Configuration</h2>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Input Mode Toggle */}
              <div className="flex items-center space-x-4 mb-4">
                <span className="text-sm font-medium text-gray-700">Input Method:</span>
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    type="button"
                    onClick={selectTextMode}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      !isUploadMode 
                        ? 'bg-white text-blue-600 shadow-sm' 
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    <FileText className="h-4 w-4 inline mr-1" />
                    Text Input
                  </button>
                  <button
                    type="button"
                    onClick={selectUploadMode}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      isUploadMode 
                        ? 'bg-white text-blue-600 shadow-sm' 
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    <Upload className="h-4 w-4 inline mr-1" />
                    PDF Upload
                  </button>
                </div>
              </div>

              {/* Input Text or File Upload */}
              {!isUploadMode ? (
                <div>
                  <label htmlFor="input_text" className="block text-sm font-medium text-gray-700 mb-2">
                    Input Text
                  </label>
                  <textarea
                    {...register('input_text', { required: !isUploadMode ? 'Input text is required' : false })}
                    rows={8}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter the text you want to test context pruning on..."
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload PDF File
                  </label>
                  
                  {!uploadedFile ? (
                    <div
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors cursor-pointer"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                      {isProcessingFile ? (
                        <div className="flex flex-col items-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                          <p className="text-sm text-gray-600">Processing PDF...</p>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center">
                          <Upload className="h-12 w-12 text-gray-400 mb-2" />
                          <p className="text-sm text-gray-600 mb-1">
                            Click to upload or drag and drop a PDF file
                          </p>
                          <p className="text-xs text-gray-500">PDF files only</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <File className="h-8 w-8 text-red-500" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                            <p className="text-xs text-gray-500">
                              {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={removeFile}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                      {fileContent && (
                        <div className="mt-3 p-3 bg-white rounded border">
                          <p className="text-xs text-gray-500 mb-1">Extracted text preview:</p>
                          <p className="text-sm text-gray-700 line-clamp-3">
                            {fileContent.substring(0, 200)}...
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Query */}
              <div>
                <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                  Query for Context Relevance
                </label>
                <input
                  {...register('query', { required: 'Query is required' })}
                  type="text"
                  value={'financial'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter a query to determine relevance (e.g., 'financial data', 'company policies')"
                />
              </div>

              {/* Method Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Pruning Methods to Test
                </label>
                <div className="space-y-2">
                  {[
                    { value: 'relevance_filter', label: 'Relevance Filter' },
                    { value: 'llm_compression', label: 'LLM Compression' },
                    { value: 'metadata_filter', label: 'Metadata Filter' },
                    { value: 'hybrid', label: 'Hybrid' }
                  ].map((method) => (
                    <label key={method.value} className="flex items-center space-x-3">
                      <input
                        {...register('methods')}
                        type="checkbox"
                        value={method.value}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="text-sm text-gray-700">{method.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Configuration */}
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
                    Top K Results
                  </label>
                  <input
                    {...register('top_k', { valueAsNumber: true })}
                    type="number"
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-md">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isProcessing || isProcessingFile || selectedMethods.length === 0}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Testing Methods...</span>
                  </>
                ) : isProcessingFile ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Processing File...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Test Context Pruning</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Results */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <BarChart3 className="h-6 w-6 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900">Results</h2>
              </div>
              {results && (
                <button
                  onClick={exportResults}
                  className="flex items-center space-x-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                >
                  <Download className="h-4 w-4" />
                  <span>Export</span>
                </button>
              )}
            </div>

            {!results ? (
              <div className="text-center py-12">
                <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Yet</h3>
                <p className="text-gray-600">Configure and run a test to see the results here.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">Test Summary</h3>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Query:</strong> {results.query}</p>
                    <p><strong>Source:</strong> {results.source}</p>
                    <p><strong>Input Length:</strong> {results.input_text.length} characters</p>
                    <p><strong>Methods Tested:</strong> {Object.keys(results.method_results).join(', ')}</p>
                    <p><strong>Timestamp:</strong> {new Date(results.timestamp).toLocaleString()}</p>
                  </div>
                </div>

                {/* Method Results */}
                {Object.entries(results.method_results).map(([method, result]) => {
                  const Icon = getMethodIcon(method);
                  const hasError = result.error;
                  
                  return (
                    <div key={method} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Icon className="h-5 w-5 text-blue-600" />
                          <h4 className="font-medium text-gray-900 capitalize">
                            {method.replace('_', ' ')}
                          </h4>
                          {hasError ? (
                            <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                              Error
                            </span>
                          ) : (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                              Success
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => setSelectedMethod(selectedMethod === method ? null : method)}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </div>

                      {hasError ? (
                        <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                          {result.error}
                        </div>
                      ) : (
                        <>
                          {/* Stats */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                            <div className="bg-blue-50 rounded p-2 text-center">
                              <div className="text-lg font-bold text-blue-600">
                                {result.stats.original_count}
                              </div>
                              <div className="text-xs text-blue-600">Original</div>
                            </div>
                            <div className="bg-green-50 rounded p-2 text-center">
                              <div className="text-lg font-bold text-green-600">
                                {result.stats.pruned_count}
                              </div>
                              <div className="text-xs text-green-600">Pruned</div>
                            </div>
                            <div className="bg-purple-50 rounded p-2 text-center">
                              <div className="text-lg font-bold text-purple-600">
                                {result.stats.efficiency}
                              </div>
                              <div className="text-xs text-purple-600">Reduction</div>
                            </div>
                            <div className="bg-orange-50 rounded p-2 text-center">
                              <div className="text-lg font-bold text-orange-600">
                                {result.stats.processing_time.toFixed(2)}s
                              </div>
                              <div className="text-xs text-orange-600">Time</div>
                            </div>
                          </div>

                          {/* Pruned Content */}
                          {selectedMethod === method && result.pruned_documents && result.pruned_documents.length > 0 && (
                            <div className="mt-4 border-t pt-4">
                              <div className="flex items-center justify-between mb-2">
                                <h5 className="font-medium text-gray-900">Pruned Content</h5>
                                <button
                                  onClick={() => copyToClipboard(result.pruned_documents.map(d => d.content).join('\n\n'))}
                                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                                  title="Copy all pruned content"
                                >
                                  <Copy className="h-4 w-4" />
                                </button>
                              </div>
                              <div className="bg-gray-50 rounded-md p-3 max-h-96 overflow-y-auto">
                                <div className="space-y-4">
                                  {result.pruned_documents.map((doc, idx) => (
                                    <div key={idx} className="border border-gray-200 rounded p-2 bg-white">
                                      <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs text-gray-500">Chunk {idx + 1}</span>
                                        {doc.metadata && doc.metadata.page_number && (
                                          <span className="text-xs text-gray-400">Page {doc.metadata.page_number}</span>
                                        )}
                                      </div>
                                      <pre className="whitespace-pre-wrap text-sm text-gray-800">
                                        {doc.content}
                                      </pre>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContextPruningTestPage;
