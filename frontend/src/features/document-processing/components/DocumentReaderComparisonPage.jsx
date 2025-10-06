import React, { useState, useEffect } from 'react'
import { FileText, Zap, Eye, AlertCircle, CheckCircle, XCircle, Loader2 } from 'lucide-react'

const DocumentReaderComparisonPage = () => {
  const [readers, setReaders] = useState({})
  const [sampleDocuments, setSampleDocuments] = useState([])
  const [selectedDocument, setSelectedDocument] = useState('')
  const [comparisonResults, setComparisonResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchReadersInfo()
  }, [])

  const fetchReadersInfo = async () => {
    try {
      const response = await fetch('/api/chat/document-reader-comparison/')
      const data = await response.json()
      
      if (data.status === 'success') {
        setReaders(data.readers)
        setSampleDocuments(data.sample_documents)
      } else {
        setError('Failed to fetch readers information')
      }
    } catch (err) {
      setError('Error fetching readers information: ' + err.message)
    }
  }

  const handleCompare = async () => {
    if (!selectedDocument) {
      setError('Please select a document to compare')
      return
    }

    setLoading(true)
    setError('')
    setComparisonResults(null)

    try {
      const response = await fetch('/api/chat/document-reader-comparison/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: selectedDocument
        })
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        setComparisonResults(data)
      } else {
        setError(data.error || 'Failed to compare document readers')
      }
    } catch (err) {
      setError('Error comparing document readers: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'unavailable':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'skipped':
        return <AlertCircle className="h-5 w-5 text-gray-500" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'unavailable':
        return 'bg-yellow-50 border-yellow-200'
      case 'skipped':
        return 'bg-gray-50 border-gray-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Document Reader Comparison
        </h1>
        <p className="text-gray-600">
          Compare different document readers on the same document to see their capabilities and differences.
        </p>
      </div>

      {/* Readers Overview */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Document Readers</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(readers).map(([key, reader]) => (
            <div key={key} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center mb-3">
                {key === 'agentic_reader' ? (
                  <Zap className="h-6 w-6 text-blue-500 mr-2" />
                ) : key === 'pdf_reader' ? (
                  <FileText className="h-6 w-6 text-green-500 mr-2" />
                ) : (
                  <Eye className="h-6 w-6 text-purple-500 mr-2" />
                )}
                <h3 className="text-lg font-medium text-gray-900">{reader.name}</h3>
              </div>
              
              <div className="mb-4">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  reader.available 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {reader.available ? 'Available' : 'Unavailable'}
                </span>
                {reader.api_key_required && (
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    API Key Required
                  </span>
                )}
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Features:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {reader.features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-500 mr-2" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Supported Formats:</h4>
                <div className="flex flex-wrap gap-1">
                  {reader.supported_formats.map((format, index) => (
                    <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {format}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Document Selection and Comparison */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Compare Document Readers</h2>
        
        <div className="mb-4">
          <label htmlFor="document-select" className="block text-sm font-medium text-gray-700 mb-2">
            Select Document to Compare
          </label>
          <select
            id="document-select"
            value={selectedDocument}
            onChange={(e) => setSelectedDocument(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Choose a document...</option>
            {sampleDocuments.map((doc, index) => (
              <option key={index} value={doc.path}>
                {doc.filename} ({doc.type.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading || !selectedDocument}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Comparing...
            </>
          ) : (
            <>
              <Eye className="h-4 w-4 mr-2" />
              Compare Readers
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {comparisonResults && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Comparison Results for {comparisonResults.file_path.split('/').pop()}
          </h2>
          
          <div className="mb-4 text-sm text-gray-600">
            <p><strong>File Type:</strong> {comparisonResults.file_type}</p>
            <p><strong>File Path:</strong> {comparisonResults.file_path}</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.entries(comparisonResults.comparison_results).map(([readerKey, result]) => (
              <div key={readerKey} className={`rounded-lg border-2 p-6 ${getStatusColor(result.status)}`}>
                <div className="flex items-center mb-4">
                  {getStatusIcon(result.status)}
                  <h3 className="text-lg font-medium text-gray-900 ml-2">
                    {readers[readerKey]?.name || readerKey}
                  </h3>
                </div>

                {result.status === 'success' && (
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-gray-700">Content Length:</p>
                      <p className="text-sm text-gray-600">{result.content_length.toLocaleString()} characters</p>
                    </div>

                    {result.structured_data_count !== undefined && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">Structured Data Chunks:</p>
                        <p className="text-sm text-gray-600">{result.structured_data_count}</p>
                      </div>
                    )}

                    {result.chunk_types && result.chunk_types.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">Chunk Types:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {result.chunk_types.map((type, index) => (
                            <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <p className="text-sm font-medium text-gray-700">Content Preview:</p>
                      <div className="mt-1 p-3 bg-gray-50 rounded border text-xs text-gray-600 max-h-32 overflow-y-auto">
                        {result.content_preview}
                      </div>
                    </div>

                    {result.metadata && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">Metadata:</p>
                        <div className="mt-1 p-3 bg-gray-50 rounded border text-xs text-gray-600 max-h-32 overflow-y-auto">
                          <pre>{JSON.stringify(result.metadata, null, 2)}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {result.status === 'error' && (
                  <div className="text-sm text-red-600">
                    <p><strong>Error:</strong> {result.error}</p>
                  </div>
                )}

                {result.status === 'unavailable' && (
                  <div className="text-sm text-yellow-600">
                    <p><strong>Reason:</strong> {result.reason}</p>
                  </div>
                )}

                {result.status === 'skipped' && (
                  <div className="text-sm text-gray-600">
                    <p><strong>Reason:</strong> {result.reason}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentReaderComparisonPage
