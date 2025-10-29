import React, { useState, useEffect } from 'react';
import { 
  FaSync, 
  FaDatabase, 
  FaSearch, 
  FaTrash, 
  FaEye, 
  FaExternalLinkAlt,
  FaCheckCircle,
  FaTimesCircle,
  FaClock,
  FaExclamationTriangle,
  FaInfoCircle
} from 'react-icons/fa';
import { API_BASE_URL } from '../../../config/api.js';
import Pagination from '../../../components/Pagination';
import ChunksViewer from './ChunksViewer';

const ConfluenceManager = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [fetching, setFetching] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [parentId, setParentId] = useState('27394188');
  const [forceRefresh, setForceRefresh] = useState(false);
  const [fetchProgress, setFetchProgress] = useState({
    isActive: false,
    current: 0,
    total: 0,
    currentDocument: '',
    status: ''
  });
  const [stats, setStats] = useState({
    total: 0,
    indexed: 0,
    outdated: 0,
    errors: 0
  });
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  
  // Chunks viewer state
  const [chunksViewer, setChunksViewer] = useState({
    isOpen: false,
    documentId: null,
    documentTitle: ''
  });

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/confluence/documents`);
      const data = await response.json();
      
      if (data.success) {
        setDocuments(data.documents);
        updateStats(data.documents);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch documents');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateStats = (docs) => {
    const stats = {
      total: docs.length,
      indexed: docs.filter(doc => doc.is_indexed).length,
      outdated: docs.filter(doc => doc.is_outdated).length,
      errors: docs.filter(doc => doc.indexing_error).length
    };
    setStats(stats);
  };

  const handleFetchFromConfluence = async () => {
    try {
      setFetching(true);
      setError(null);
      setFetchProgress({
        isActive: true,
        current: 0,
        total: 0,
        currentDocument: 'Starting fetch...',
        status: 'Connecting to Confluence...'
      });
      
      console.log('Starting Confluence fetch...');
      
      const response = await fetch(`${API_BASE_URL}/confluence/fetch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          parent_id: parentId,
          force_refresh: forceRefresh
        })
      });
      
      const data = await response.json();
      console.log('Confluence fetch response:', data);
      
      if (data.success) {
        setFetchProgress({
          isActive: false,
          current: 0,
          total: 0,
          currentDocument: '',
          status: 'Fetch completed!'
        });
        
        // Refresh the documents list
        await fetchDocuments();
        
        // Show success message with details
        const processingDetails = data.processing_details;
        let message = `Successfully processed ${data.stats.new_documents + data.stats.updated_documents} documents:\n` +
          `• New documents: ${data.stats.new_documents}\n` +
          `• Updated documents: ${data.stats.updated_documents}\n` +
          `• Errors: ${data.stats.errors}\n\n` +
          `Processing Details:\n` +
          `• Total pages found: ${processingDetails.total_pages_found}\n` +
          `• Pages processed: ${processingDetails.total_pages_processed}`;
        
        if (processingDetails.pages_processed && processingDetails.pages_processed.length > 0) {
          message += `\n\nLast processed pages:\n`;
          processingDetails.pages_processed.forEach((page, index) => {
            message += `• ${page.title}\n`;
          });
        }
        
        alert(message);
      } else {
        setError(data.error);
        setFetchProgress({
          isActive: false,
          current: 0,
          total: 0,
          currentDocument: '',
          status: 'Fetch failed'
        });
      }
    } catch (err) {
      setError('Failed to fetch from Confluence');
      console.error('Error fetching from Confluence:', err);
      setFetchProgress({
        isActive: false,
        current: 0,
        total: 0,
        currentDocument: '',
        status: 'Fetch failed'
      });
    } finally {
      setFetching(false);
    }
  };

  const handleIndexDocuments = async (documentIds = null) => {
    try {
      setIndexing(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/confluence/index`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_ids: documentIds || selectedDocuments,
          force_reindex: true
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh the documents list
        await fetchDocuments();
        alert(`Successfully indexed ${data.stats.successfully_indexed} documents`);
        setSelectedDocuments([]);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to index documents');
      console.error('Error indexing documents:', err);
    } finally {
      setIndexing(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/confluence/documents/${documentId}/delete`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      
      if (data.success) {
        await fetchDocuments();
        alert('Document deleted successfully');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to delete document');
      console.error('Error deleting document:', err);
    }
  };

  const toggleDocumentSelection = (documentId) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const selectAllDocuments = () => {
    setSelectedDocuments(documents.map(doc => doc.id));
  };

  const clearSelection = () => {
    setSelectedDocuments([]);
  };

  // Pagination functions
  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Reset to first page
  };

  // Chunks viewer functions
  const openChunksViewer = (documentId, documentTitle) => {
    setChunksViewer({
      isOpen: true,
      documentId,
      documentTitle
    });
  };

  const closeChunksViewer = () => {
    setChunksViewer({
      isOpen: false,
      documentId: null,
      documentTitle: ''
    });
  };

  // Get paginated documents
  const getPaginatedDocuments = () => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return documents.slice(startIndex, endIndex);
  };

  const totalPages = Math.ceil(documents.length / itemsPerPage);

  const getStatusIcon = (document) => {
    if (document.indexing_error) {
      return <FaTimesCircle className="text-red-500" title="Indexing Error" />;
    }
    if (document.is_indexed) {
      return <FaCheckCircle className="text-green-500" title="Indexed" />;
    }
    if (document.is_outdated) {
      return <FaExclamationTriangle className="text-yellow-500" title="Outdated" />;
    }
    return <FaClock className="text-gray-400" title="Not Indexed" />;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Confluence Document Manager</h1>
        <p className="text-gray-600">Manage and index documents from your Confluence workspace</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <FaTimesCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaDatabase className="h-6 w-6 text-blue-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.total}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaCheckCircle className="h-6 w-6 text-green-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Indexed</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.indexed}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaExclamationTriangle className="h-6 w-6 text-yellow-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Outdated</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.outdated}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaTimesCircle className="h-6 w-6 text-red-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Errors</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.errors}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Display */}
      {fetchProgress.isActive && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-sm font-medium text-blue-800">Fetching from Confluence</h3>
              <div className="mt-2">
                <div className="text-sm text-blue-700">{fetchProgress.status}</div>
                {fetchProgress.currentDocument && (
                  <div className="text-sm text-blue-600 mt-1">
                    Processing: {fetchProgress.currentDocument}
                  </div>
                )}
                {fetchProgress.total > 0 && (
                  <div className="text-sm text-blue-600 mt-1">
                    Progress: {fetchProgress.current} / {fetchProgress.total} documents
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Actions</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Fetch from Confluence */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Fetch from Confluence</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Parent Page ID
                </label>
                <input
                  type="text"
                  value={parentId}
                  onChange={(e) => setParentId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="27394188"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="forceRefresh"
                  checked={forceRefresh}
                  onChange={(e) => setForceRefresh(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="forceRefresh" className="ml-2 block text-sm text-gray-700">
                  Force refresh existing documents
                </label>
              </div>
              <button
                onClick={handleFetchFromConfluence}
                disabled={fetching}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {fetching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Fetching...
                  </>
                ) : (
                  <>
                    <FaSync className="mr-2" />
                    Fetch from Confluence
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Index Documents */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Index Documents</h3>
            <div className="space-y-3">
              <div className="flex space-x-2">
                <button
                  onClick={selectAllDocuments}
                  className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded-md hover:bg-gray-200 text-sm"
                >
                  Select All
                </button>
                <button
                  onClick={clearSelection}
                  className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded-md hover:bg-gray-200 text-sm"
                >
                  Clear
                </button>
              </div>
              <div className="text-sm text-gray-600">
                {selectedDocuments.length} document(s) selected
              </div>
              <button
                onClick={() => handleIndexDocuments()}
                disabled={indexing || selectedDocuments.length === 0}
                className="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {indexing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Indexing...
                  </>
                ) : (
                  <>
                    <FaDatabase className="mr-2" />
                    Index Selected Documents
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Documents</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.length === documents.length && documents.length > 0}
                    onChange={(e) => e.target.checked ? selectAllDocuments() : clearSelection()}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Space
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Modified
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {getPaginatedDocuments().map((document) => (
                <tr key={document.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.includes(document.id)}
                      onChange={() => toggleDocumentSelection(document.id)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(document)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                      {document.title}
                    </div>
                    <div className="text-sm text-gray-500">
                      ID: {document.confluence_id}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {document.space_name || document.space_key}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(document.confluence_modified)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <a
                        href={document.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                        title="View in Confluence"
                      >
                        <FaExternalLinkAlt />
                      </a>
                      {document.is_indexed && (
                        <button
                          onClick={() => openChunksViewer(document.id, document.title)}
                          className="text-purple-600 hover:text-purple-900"
                          title="View Chunks"
                        >
                          <FaEye />
                        </button>
                      )}
                      <button
                        onClick={() => handleIndexDocuments([document.id])}
                        className="text-green-600 hover:text-green-900"
                        title="Index Document"
                      >
                        <FaDatabase />
                      </button>
                      <button
                        onClick={() => handleDeleteDocument(document.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete Document"
                      >
                        <FaTrash />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {documents.length === 0 && (
          <div className="text-center py-12">
            <FaInfoCircle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by fetching documents from Confluence.
            </p>
          </div>
        )}

        {/* Pagination */}
        {documents.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            itemsPerPage={itemsPerPage}
            totalItems={documents.length}
            onItemsPerPageChange={handleItemsPerPageChange}
          />
        )}
      </div>

      {/* Chunks Viewer Modal */}
      <ChunksViewer
        documentId={chunksViewer.documentId}
        documentTitle={chunksViewer.documentTitle}
        isOpen={chunksViewer.isOpen}
        onClose={closeChunksViewer}
      />
    </div>
  );
};

export default ConfluenceManager;
