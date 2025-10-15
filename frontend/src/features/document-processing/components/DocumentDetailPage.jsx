import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  FaArrowLeft, 
  FaFileAlt,
  FaFilePdf,
  FaFileWord,
  FaCopy,
  FaCheckCircle,
  FaSearch
} from 'react-icons/fa';

const API_BASE_URL = 'http://localhost:8000/api';

const DocumentDetailPage = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  
  const [document, setDocument] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedChunk, setSelectedChunk] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedChunkId, setCopiedChunkId] = useState(null);

  useEffect(() => {
    fetchDocumentDetails();
    fetchDocumentChunks();
  }, [documentId]);

  const fetchDocumentDetails = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/document-processing/documents/${documentId}/`);
      if (!response.ok) throw new Error('Failed to fetch document details');
      const data = await response.json();
      setDocument(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchDocumentChunks = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/document-processing/documents/${documentId}/chunks/`);
      if (!response.ok) throw new Error('Failed to fetch document chunks');
      const data = await response.json();
      setChunks(data.chunks || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyChunk = (chunkId, content) => {
    navigator.clipboard.writeText(content);
    setCopiedChunkId(chunkId);
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'pdf':
        return <FaFilePdf className="text-red-500 text-4xl" />;
      case 'docx':
        return <FaFileWord className="text-blue-500 text-4xl" />;
      default:
        return <FaFileAlt className="text-gray-500 text-4xl" />;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredChunks = chunks.filter(chunk =>
    chunk.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading && !document) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/documents')}
          className="flex items-center text-blue-600 hover:text-blue-700 mb-4"
        >
          <FaArrowLeft className="mr-2" />
          Back to Documents
        </button>
        
        {document && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start space-x-4">
              <div className="mt-1">
                {getFileIcon(document.file_type)}
              </div>
              
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                  {document.name}
                </h1>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div>
                    <p className="text-sm text-gray-500">File Size</p>
                    <p className="text-lg font-semibold">{document.file_size_mb} MB</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">File Type</p>
                    <p className="text-lg font-semibold uppercase">{document.file_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Upload Date</p>
                    <p className="text-lg font-semibold">
                      {formatDate(document.upload_date)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Chunks</p>
                    <p className="text-lg font-semibold">{chunks.length}</p>
                  </div>
                </div>

                {document.metadata?.chunks_count && (
                  <div className="mt-4 flex items-center text-green-600">
                    <FaCheckCircle className="mr-2" />
                    <span>Processed and indexed in ChromaDB</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chunks Section */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Document Chunks ({filteredChunks.length})
            </h2>
            
            <div className="relative">
              <input
                type="text"
                placeholder="Search chunks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <FaSearch className="absolute left-3 top-3 text-gray-400" />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="px-6 py-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading chunks...</p>
          </div>
        ) : filteredChunks.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            <p className="text-lg">
              {searchTerm ? 'No chunks match your search' : 'No chunks found'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredChunks.map((chunk, index) => (
              <div
                key={chunk.chunk_id}
                className={`px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                  selectedChunk?.chunk_id === chunk.chunk_id ? 'bg-blue-50' : ''
                }`}
                onClick={() => setSelectedChunk(chunk)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-semibold rounded-full">
                        Chunk {chunk.chunk_index + 1}
                      </span>
                      <span className="text-sm text-gray-500">
                        ID: {chunk.chunk_id}
                      </span>
                    </div>
                    
                    <div className="text-gray-700 line-clamp-3">
                      {chunk.content}
                    </div>

                    {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                      <div className="mt-2 text-sm text-gray-500">
                        <strong>Metadata:</strong>{' '}
                        {Object.entries(chunk.metadata)
                          .filter(([key]) => !['chunk_id', 'chunk_index', 'document_id', 'document_name'].includes(key))
                          .map(([key, value]) => `${key}: ${value}`)
                          .join(', ')}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopyChunk(chunk.chunk_id, chunk.content);
                    }}
                    className="ml-4 p-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
                    title="Copy to clipboard"
                  >
                    {copiedChunkId === chunk.chunk_id ? (
                      <FaCheckCircle className="text-green-500" />
                    ) : (
                      <FaCopy />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Chunk Detail Modal */}
      {selectedChunk && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedChunk(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-xl font-semibold">
                Chunk {selectedChunk.chunk_index + 1} Details
              </h3>
              <button
                onClick={() => setSelectedChunk(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto max-h-[calc(80vh-120px)]">
              <div className="mb-4">
                <p className="text-sm text-gray-500 mb-1">Chunk ID</p>
                <p className="font-mono text-sm bg-gray-100 p-2 rounded">
                  {selectedChunk.chunk_id}
                </p>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-500 mb-1">Content</p>
                <div className="bg-gray-50 p-4 rounded-lg whitespace-pre-wrap">
                  {selectedChunk.content}
                </div>
              </div>

              {selectedChunk.metadata && (
                <div className="mb-4">
                  <p className="text-sm text-gray-500 mb-1">Metadata</p>
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <pre className="text-sm overflow-x-auto">
                      {JSON.stringify(selectedChunk.metadata, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              <button
                onClick={() => handleCopyChunk(selectedChunk.chunk_id, selectedChunk.content)}
                className="w-full mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center"
              >
                {copiedChunkId === selectedChunk.chunk_id ? (
                  <>
                    <FaCheckCircle className="mr-2" />
                    Copied!
                  </>
                ) : (
                  <>
                    <FaCopy className="mr-2" />
                    Copy Content
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>💡 About Chunks:</strong> Documents are automatically split into chunks for better retrieval.
          Each chunk is embedded and stored in ChromaDB for hybrid search (Vector + BM25).
        </p>
      </div>
    </div>
  );
};

export default DocumentDetailPage;

