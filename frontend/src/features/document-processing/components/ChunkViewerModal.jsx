import React, { useState, useMemo } from 'react';
import { 
  X, 
  Search, 
  Filter, 
  Download, 
  Copy, 
  Eye, 
  EyeOff,
  ChevronDown,
  ChevronUp,
  FileText,
  Table,
  List,
  Hash,
  Clock,
  BarChart3,
  Settings
} from 'lucide-react';
import { cleanChunkContent, formatChunkContent } from '../utils/contentUtils';

const ChunkViewerModal = ({ isOpen, onClose, results, title = "Chunk Analysis" }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedChunkType, setSelectedChunkType] = useState('all');
  const [selectedMethod, setSelectedMethod] = useState('all');
  const [expandedChunks, setExpandedChunks] = useState(new Set());
  const [sortBy, setSortBy] = useState('chunk_index');
  const [sortOrder, setSortOrder] = useState('asc');
  const [viewMode, setViewMode] = useState('detailed'); // detailed, compact, table

  // Get unique chunk types and methods
  const chunkTypes = useMemo(() => {
    const types = new Set();
    results?.forEach(result => {
      result.chunks?.forEach(chunk => types.add(chunk.chunk_type));
    });
    return Array.from(types);
  }, [results]);

  const methods = useMemo(() => {
    return results?.map(result => ({
      id: result.id,
      name: result.chunking_method?.name || 'Unknown Method'
    })) || [];
  }, [results]);

  // Filter and sort chunks
  const filteredAndSortedChunks = useMemo(() => {
    if (!results) return [];

    let allChunks = [];
    results.forEach(result => {
      result.chunks?.forEach(chunk => {
        allChunks.push({
          ...chunk,
          methodName: result.chunking_method?.name || 'Unknown',
          methodId: result.id,
          resultId: result.id
        });
      });
    });

    // Filter by search term
    if (searchTerm) {
      allChunks = allChunks.filter(chunk => 
        chunk.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        chunk.chunk_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        chunk.methodName.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by chunk type
    if (selectedChunkType !== 'all') {
      allChunks = allChunks.filter(chunk => chunk.chunk_type === selectedChunkType);
    }

    // Filter by method
    if (selectedMethod !== 'all') {
      allChunks = allChunks.filter(chunk => chunk.methodId === selectedMethod);
    }

    // Sort
    allChunks.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];
      
      if (sortBy === 'content') {
        aVal = a.content.length;
        bVal = b.content.length;
      }
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return allChunks;
  }, [results, searchTerm, selectedChunkType, selectedMethod, sortBy, sortOrder]);

  const toggleChunkExpansion = (chunkId) => {
    const newExpanded = new Set(expandedChunks);
    if (newExpanded.has(chunkId)) {
      newExpanded.delete(chunkId);
    } else {
      newExpanded.add(chunkId);
    }
    setExpandedChunks(newExpanded);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };


  const exportChunks = (format = 'json') => {
    const data = filteredAndSortedChunks.map(chunk => ({
      id: chunk.id,
      method: chunk.methodName,
      type: chunk.chunk_type,
      index: chunk.chunk_index,
      content: chunk.content,
      token_count: chunk.token_count,
      metadata: chunk.metadata
    }));

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chunks_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
    } else if (format === 'csv') {
      const csvContent = [
        ['Method', 'Type', 'Index', 'Token Count', 'Content'],
        ...data.map(chunk => [
          chunk.method,
          chunk.type,
          chunk.index,
          chunk.token_count,
          `"${chunk.content.replace(/"/g, '""')}"`
        ])
      ].map(row => row.join(',')).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chunks_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
    }
  };

  const getChunkTypeIcon = (type) => {
    switch (type) {
      case 'table': return <Table className="h-4 w-4" />;
      case 'header': return <Hash className="h-4 w-4" />;
      case 'list': return <List className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getChunkTypeColor = (type) => {
    switch (type) {
      case 'table': return 'bg-blue-100 text-blue-800';
      case 'header': return 'bg-purple-100 text-purple-800';
      case 'list': return 'bg-green-100 text-green-800';
      case 'text': return 'bg-gray-100 text-gray-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
              <p className="text-gray-600 mt-1">
                {filteredAndSortedChunks.length} chunks from {methods.length} method{methods.length > 1 ? 's' : ''}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => exportChunks('json')}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export JSON</span>
              </button>
              <button
                onClick={() => exportChunks('csv')}
                className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Filters and Controls */}
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search chunks..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Chunk Type Filter */}
              <select
                value={selectedChunkType}
                onChange={(e) => setSelectedChunkType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                {chunkTypes.map(type => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>

              {/* Method Filter */}
              <select
                value={selectedMethod}
                onChange={(e) => setSelectedMethod(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Methods</option>
                {methods.map(method => (
                  <option key={method.id} value={method.id}>
                    {method.name}
                  </option>
                ))}
              </select>

              {/* Sort */}
              <div className="flex space-x-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="chunk_index">Index</option>
                  <option value="token_count">Token Count</option>
                  <option value="content">Content Length</option>
                  <option value="chunk_type">Type</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  {sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center space-x-2 mt-4">
              <span className="text-sm text-gray-600">View:</span>
              <div className="flex border border-gray-300 rounded-md">
                <button
                  onClick={() => setViewMode('detailed')}
                  className={`px-3 py-1 text-sm ${viewMode === 'detailed' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                >
                  Detailed
                </button>
                <button
                  onClick={() => setViewMode('compact')}
                  className={`px-3 py-1 text-sm ${viewMode === 'compact' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                >
                  Compact
                </button>
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-3 py-1 text-sm ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}`}
                >
                  Table
                </button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {filteredAndSortedChunks.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No chunks found</h3>
                <p className="text-gray-600">Try adjusting your search or filter criteria.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredAndSortedChunks.map((chunk) => {
                  const isExpanded = expandedChunks.has(chunk.id);
                  const shouldTruncate = !isExpanded && chunk.content.length > 300;

                  return (
                    <div
                      key={chunk.id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      {/* Chunk Header */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getChunkTypeColor(chunk.chunk_type)}`}>
                            {getChunkTypeIcon(chunk.chunk_type)}
                            <span>{chunk.chunk_type}</span>
                          </div>
                          <span className="text-sm text-gray-600">#{chunk.chunk_index}</span>
                          <span className="text-sm text-gray-500">•</span>
                          <span className="text-sm text-gray-600">{chunk.methodName}</span>
                          <span className="text-sm text-gray-500">•</span>
                          <span className="text-sm text-gray-600">{chunk.token_count} tokens</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => copyToClipboard(chunk.content)}
                            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                            title="Copy content"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => toggleChunkExpansion(chunk.id)}
                            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                            title={isExpanded ? "Collapse" : "Expand"}
                          >
                            {isExpanded ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>

                      {/* Chunk Content */}
                      <div className="bg-gray-50 rounded-md p-3">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                          {shouldTruncate ? cleanChunkContent(chunk.content).substring(0, 300) + '...' : cleanChunkContent(chunk.content)}
                        </pre>
                        {shouldTruncate && (
                          <button
                            onClick={() => toggleChunkExpansion(chunk.id)}
                            className="text-blue-600 hover:text-blue-800 text-sm mt-2"
                          >
                            Show more
                          </button>
                        )}
                      </div>

                      {/* Metadata */}
                      {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <details className="group">
                            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                              <Settings className="h-4 w-4 inline mr-1" />
                              Metadata
                            </summary>
                            <div className="mt-2 bg-gray-100 rounded p-2">
                              <pre className="text-xs text-gray-700">
                                {JSON.stringify(chunk.metadata, null, 2)}
                              </pre>
                            </div>
                          </details>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Showing {filteredAndSortedChunks.length} of {results?.reduce((sum, result) => sum + (result.chunks?.length || 0), 0)} chunks
              </div>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChunkViewerModal;
