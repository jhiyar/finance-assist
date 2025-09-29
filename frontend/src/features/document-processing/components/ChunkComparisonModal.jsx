import React, { useState } from 'react';
import { X, Eye, EyeOff, FileText, Scissors, ArrowRight, Search, Filter } from 'lucide-react';
import { formatChunkContent } from '../utils/contentUtils';

const ChunkComparisonModal = ({ isOpen, onClose, pruningResult }) => {
  const [selectedChunkIndex, setSelectedChunkIndex] = useState(0);
  const [showOriginal, setShowOriginal] = useState(true);
  const [showPruned, setShowPruned] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMethod, setFilterMethod] = useState('all');

  if (!isOpen || !pruningResult) return null;

  const { original_documents = [], pruned_documents = [], stats, metadata } = pruningResult;

  // Filter chunks based on search term and method
  const filteredOriginalChunks = original_documents.filter(chunk => {
    const matchesSearch = !searchTerm || 
      chunk.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (chunk.metadata?.chunking_method && chunk.metadata.chunking_method.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesMethod = filterMethod === 'all' || 
      (chunk.metadata?.chunking_method === filterMethod);
    
    return matchesSearch && matchesMethod;
  });

  const filteredPrunedChunks = pruned_documents.filter(chunk => {
    const matchesSearch = !searchTerm || 
      chunk.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (chunk.metadata?.chunking_method && chunk.metadata.chunking_method.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesMethod = filterMethod === 'all' || 
      (chunk.metadata?.chunking_method === filterMethod);
    
    return matchesSearch && matchesMethod;
  });

  // Get unique chunking methods for filter
  const chunkingMethods = [...new Set([
    ...original_documents.map(doc => doc.metadata?.chunking_method).filter(Boolean),
    ...pruned_documents.map(doc => doc.metadata?.chunking_method).filter(Boolean)
  ])];

  const currentOriginalChunk = filteredOriginalChunks[selectedChunkIndex];
  const currentPrunedChunk = filteredPrunedChunks[selectedChunkIndex];


  const getChunkMetadata = (chunk) => {
    if (!chunk?.metadata) return {};
    return {
      method: chunk.metadata.chunking_method || 'Unknown',
      type: chunk.metadata.chunk_type || 'text',
      index: chunk.metadata.chunk_index || 'N/A',
      tokens: chunk.metadata.token_count || 'N/A',
      position: chunk.metadata.start_position ? 
        `${chunk.metadata.start_position}-${chunk.metadata.end_position}` : 'N/A'
    };
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Scissors className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Chunk Comparison</h2>
              <p className="text-sm text-gray-600">
                Compare original vs pruned chunks • {stats.original_count} → {stats.pruned_count} chunks
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Controls */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex flex-wrap items-center gap-4">
            {/* Search */}
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search chunks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Filter by method */}
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={filterMethod}
                onChange={(e) => setFilterMethod(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Methods</option>
                {chunkingMethods.map(method => (
                  <option key={method} value={method}>{method}</option>
                ))}
              </select>
            </div>

            {/* Toggle views */}
            <div className="flex items-center space-x-2 ml-auto">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                  showOriginal ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                }`}
              >
                {showOriginal ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                <span>Original ({filteredOriginalChunks.length})</span>
              </button>
              <button
                onClick={() => setShowPruned(!showPruned)}
                className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                  showPruned ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                }`}
              >
                {showPruned ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                <span>Pruned ({filteredPrunedChunks.length})</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chunk Navigation */}
          <div className="w-64 border-r border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Chunk Navigation</h3>
              <div className="space-y-2">
                {Array.from({ length: Math.max(filteredOriginalChunks.length, filteredPrunedChunks.length) }, (_, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedChunkIndex(index)}
                    className={`w-full text-left p-2 rounded-md text-sm transition-colors ${
                      selectedChunkIndex === index
                        ? 'bg-blue-100 text-blue-700 border border-blue-200'
                        : 'hover:bg-gray-100 text-gray-600'
                    }`}
                  >
                    <div className="font-medium">Chunk {index + 1}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {filteredOriginalChunks[index] && (
                        <span className="text-blue-600">O: {getChunkMetadata(filteredOriginalChunks[index]).method}</span>
                      )}
                      {filteredOriginalChunks[index] && filteredPrunedChunks[index] && ' • '}
                      {filteredPrunedChunks[index] && (
                        <span className="text-green-600">P: {getChunkMetadata(filteredPrunedChunks[index]).method}</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Chunk Content */}
          <div className="flex-1 flex">
            {/* Original Chunk */}
            {showOriginal && (
              <div className="flex-1 border-r border-gray-200 flex flex-col">
                <div className="p-4 border-b border-gray-200 bg-blue-50">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-blue-600" />
                    <h3 className="font-medium text-blue-900">Original Chunk</h3>
                    {currentOriginalChunk && (
                      <span className="text-sm text-blue-600">
                        ({getChunkMetadata(currentOriginalChunk).method})
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex-1 p-4 overflow-y-auto">
                  {currentOriginalChunk ? (
                    <div>
                      <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Type:</span> {getChunkMetadata(currentOriginalChunk).type}
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Index:</span> {getChunkMetadata(currentOriginalChunk).index}
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Tokens:</span> {getChunkMetadata(currentOriginalChunk).tokens}
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Position:</span> {getChunkMetadata(currentOriginalChunk).position}
                        </div>
                      </div>
                      <div className="prose max-w-none">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-md border">
                          {formatChunkContent(currentOriginalChunk.content)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <FileText className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>No original chunk at this index</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Arrow */}
            {showOriginal && showPruned && (
              <div className="flex items-center justify-center p-4 bg-gray-50">
                <ArrowRight className="h-6 w-6 text-gray-400" />
              </div>
            )}

            {/* Pruned Chunk */}
            {showPruned && (
              <div className="flex-1 flex flex-col">
                <div className="p-4 border-b border-gray-200 bg-green-50">
                  <div className="flex items-center space-x-2">
                    <Scissors className="h-5 w-5 text-green-600" />
                    <h3 className="font-medium text-green-900">Pruned Chunk</h3>
                    {currentPrunedChunk && (
                      <span className="text-sm text-green-600">
                        ({getChunkMetadata(currentPrunedChunk).method})
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex-1 p-4 overflow-y-auto">
                  {currentPrunedChunk ? (
                    <div>
                      <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Type:</span> {getChunkMetadata(currentPrunedChunk).type}
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Index:</span> {getChunkMetadata(currentPrunedChunk).index}
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Tokens:</span> {getChunkMetadata(currentPrunedChunk).tokens}
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Position:</span> {getChunkMetadata(currentPrunedChunk).position}
                        </div>
                      </div>
                      <div className="prose max-w-none">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-md border">
                          {formatChunkContent(currentPrunedChunk.content)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      <Scissors className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>No pruned chunk at this index</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer with stats */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-6">
              <span><strong>Method:</strong> {stats.pruning_method}</span>
              <span><strong>Compression:</strong> {stats.efficiency}</span>
              <span><strong>Processing Time:</strong> {stats.processing_time.toFixed(2)}s</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>Query: {metadata?.query || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChunkComparisonModal;
