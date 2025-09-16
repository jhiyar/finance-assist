import React from 'react'
import Modal from '../../core/components/Modal'
import MarkdownWidget from '../../core/components/MarkdownWidget'

function RAGDetailsModal({ open, onClose, ragDetails }) {
  if (!open || !ragDetails) return null

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  return (
    <Modal open={open} title="RAG Analysis Details" onClose={onClose} size="xl">
      <div className="space-y-6">
        {/* Overview */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3 text-gray-900">Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(ragDetails.confidence)}`}>
                {Math.round(ragDetails.confidence * 100)}% Confidence
              </div>
              <p className="text-sm text-gray-600 mt-1">Overall Confidence</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{ragDetails.citations?.length || 0}</div>
              <p className="text-sm text-gray-600">Citations</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{ragDetails.sources_used?.length || 0}</div>
              <p className="text-sm text-gray-600">Sources Used</p>
            </div>
          </div>
        </div>

        {/* Processing Information */}
        {ragDetails.rag_details?.processing_info && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">Processing Information</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="font-medium text-gray-700">Optimized Query</p>
                <p className="text-gray-600">{ragDetails.rag_details.processing_info.optimized_query || 'N/A'}</p>
              </div>
              <div>
                <p className="font-medium text-gray-700">Documents Selected</p>
                <p className="text-gray-600">{ragDetails.rag_details.processing_info.documents_selected || 0}</p>
              </div>
              <div>
                <p className="font-medium text-gray-700">Documents Retrieved</p>
                <p className="text-gray-600">{ragDetails.rag_details.processing_info.documents_retrieved || 0}</p>
              </div>
              <div>
                <p className="font-medium text-gray-700">Documents Processed</p>
                <p className="text-gray-600">{ragDetails.rag_details.processing_info.documents_processed || 0}</p>
              </div>
            </div>
          </div>
        )}

        {/* Confidence Scores */}
        {ragDetails.rag_details?.confidence_scores && (
          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">Confidence Scores</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(ragDetails.rag_details.confidence_scores).map(([key, value]) => (
                <div key={key} className="text-center">
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(value)}`}>
                    {Math.round(value * 100)}%
                  </div>
                  <p className="text-sm text-gray-600 mt-1 capitalize">{key.replace('_', ' ')}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reasoning */}
        {ragDetails.rag_details?.reasoning && (
          <div className="bg-yellow-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">Reasoning</h3>
            <div className="space-y-3">
              {Object.entries(ragDetails.rag_details.reasoning).map(([key, value]) => (
                <div key={key}>
                  <p className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}</p>
                  <div className="text-sm text-gray-600 mt-1">
                    <MarkdownWidget content={value} isUser={false} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Citations */}
        {ragDetails.citations && ragDetails.citations.length > 0 && (
          <div className="bg-purple-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">Citations</h3>
            <div className="space-y-3 max-h-60 overflow-y-auto">
              {ragDetails.citations.map((citation, index) => (
                <div key={index} className="bg-white rounded-lg p-3 border border-purple-200">
                  <div className="flex items-start justify-between mb-2">
                    <span className="bg-purple-100 text-purple-800 text-xs font-medium px-2 py-1 rounded">
                      Citation {citation.id}
                    </span>
                    <span className="text-xs text-gray-500">{citation.source}</span>
                  </div>
                  <div className="text-sm text-gray-700 line-clamp-3">
                    <MarkdownWidget content={citation.content} isUser={false} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sources Used */}
        {ragDetails.sources_used && ragDetails.sources_used.length > 0 && (
          <div className="bg-indigo-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">Sources Used</h3>
            <div className="space-y-2">
              {ragDetails.sources_used.map((source, index) => (
                <div key={index} className="bg-white rounded-lg p-3 border border-indigo-200">
                  <p className="text-sm text-gray-700 font-mono">{source}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3 text-gray-900">Metadata</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-gray-700">Timestamp</p>
              <p className="text-gray-600">{formatTimestamp(ragDetails.rag_details?.timestamp)}</p>
            </div>
            <div>
              <p className="font-medium text-gray-700">Source</p>
              <p className="text-gray-600">{ragDetails.source || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export default RAGDetailsModal
