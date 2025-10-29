import React, { useState, useEffect } from 'react';
import { 
  FaDatabase, 
  FaEye, 
  FaTimes, 
  FaSearch,
  FaCopy,
  FaCheck
} from 'react-icons/fa';
import { API_BASE_URL } from '../../../config/api.js';

const ChunksViewer = ({ documentId, documentTitle, isOpen, onClose }) => {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedChunk, setCopiedChunk] = useState(null);

  useEffect(() => {
    if (isOpen && documentId) {
      fetchChunks();
    }
  }, [isOpen, documentId]);

  const fetchChunks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/confluence/documents/${documentId}/chunks`);
      const data = await response.json();
      
      if (data.success) {
        setChunks(data.chunks || []);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch chunks');
      console.error('Error fetching chunks:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text, chunkId) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedChunk(chunkId);
      setTimeout(() => setCopiedChunk(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const filteredChunks = chunks.filter(chunk =>
    chunk.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chunk.metadata?.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" onClick={onClose}>
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <FaDatabase className="h-6 w-6 text-blue-500 mr-2" />
                <h3 className="text-lg font-medium text-gray-900">
                  Chunks for: {documentTitle}
                </h3>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <FaTimes className="h-6 w-6" />
              </button>
            </div>

            {/* Search and Stats */}
            <div className="mb-4">
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <div className="relative">
                    <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      type="text"
                      placeholder="Search chunks..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  {filteredChunks.length} of {chunks.length} chunks
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                <div className="text-sm text-red-700">{error}</div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-gray-600">Loading chunks...</span>
              </div>
            )}

            {/* Chunks List */}
            {!loading && !error && (
              <div className="max-h-96 overflow-y-auto">
                {filteredChunks.length === 0 ? (
                  <div className="text-center py-8">
                    <FaDatabase className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No chunks found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchTerm ? 'No chunks match your search.' : 'This document has not been indexed yet.'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredChunks.map((chunk, index) => (
                      <div key={chunk.chunk_id || index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Chunk {chunk.chunk_index || index + 1}
                              </span>
                              {chunk.metadata?.title && (
                                <span className="text-sm text-gray-600">
                                  {chunk.metadata.title}
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-900 whitespace-pre-wrap">
                              {chunk.content}
                            </div>
                            {chunk.metadata && (
                              <div className="mt-2 text-xs text-gray-500">
                                <div className="flex flex-wrap gap-2">
                                  {Object.entries(chunk.metadata).map(([key, value]) => (
                                    <span key={key} className="bg-gray-100 px-2 py-1 rounded">
                                      {key}: {String(value)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => copyToClipboard(chunk.content, chunk.chunk_id)}
                            className="ml-2 p-2 text-gray-400 hover:text-gray-600"
                            title="Copy chunk content"
                          >
                            {copiedChunk === chunk.chunk_id ? (
                              <FaCheck className="h-4 w-4 text-green-500" />
                            ) : (
                              <FaCopy className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChunksViewer;
