import React, { useState } from 'react';
import { Message, MESSAGE_TYPES } from '../models/conversation.js';
import { 
  FileText,
  Info,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import MarkdownWidget from '../../core/components/MarkdownWidget.jsx';

const MessageBubble = ({ message, showTimestamp = false }) => {
  const [showDetails, setShowDetails] = useState(false);

  if (!message || !(message instanceof Message)) {
    return null;
  }

  const isUser = message.isUserMessage();
  const isAssistant = message.isAssistantMessage();
  const hasRAGMetadata = message.hasRAGMetadata();

  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        <>
          {/* Message Bubble */}
          <div
            className={`rounded-lg px-4 py-3 ${
              isUser
                ? 'bg-blue-400 text-white'
                : isAssistant
                ? 'bg-white border border-gray-200 text-gray-900'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {/* Message Content */}
            <div className={`prose prose-sm max-w-none ${isUser ? 'text-white' : ''}`}>
              <MarkdownWidget content={message.content} />
            </div>

            {/* Timestamp */}
            {showTimestamp && (
              <div className={`text-xs mt-2 ${
                isUser ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {message.getFormattedTime()}
              </div>
            )}
          </div>

          {/* RAG Metadata */}
          {isAssistant && hasRAGMetadata && (
            <div className="mt-2">
            <button
              onClick={toggleDetails}
              className="flex items-center text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              {showDetails ? (
                <ChevronDown className="h-3 w-3 mr-1" />
              ) : (
                <ChevronRight className="h-3 w-3 mr-1" />
              )}
              <Info className="h-3 w-3 mr-1" />
              Response Details
            </button>

            {showDetails && (
              <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-md text-xs">
                {/* Source Information */}
                <div className="mb-3">
                  <div className="flex items-center mb-1">
                    <span className="font-medium text-gray-700">Source:</span>
                    <span className="ml-2 text-gray-600">{message.getSourceDisplay()}</span>
                  </div>
                  {message.retriever_type && (
                    <div className="flex items-center">
                      <span className="font-medium text-gray-700">Method:</span>
                      <span className="ml-2 text-gray-600">{message.getRetrieverTypeDisplay()}</span>
                    </div>
                  )}
                  {message.confidence && (
                    <div className="flex items-center">
                      <span className="font-medium text-gray-700">Confidence:</span>
                      <span className="ml-2 text-gray-600">
                        {(message.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mb-3">
                    <div className="flex items-center mb-2">
                      <FileText className="h-3 w-3 mr-1" />
                      <span className="font-medium text-gray-700">Sources ({message.sources.length})</span>
                    </div>
                    <div className="space-y-1">
                      {message.sources.slice(0, 3).map((source, index) => (
                        <div key={index} className="text-gray-600">
                          <div className="font-medium">{source.document_name || `Source ${index + 1}`}</div>
                          <div className="text-gray-500 truncate">
                            {source.content_preview}
                          </div>
                          {source.hybrid_score && (
                            <div className="text-gray-400">
                              Score: {source.hybrid_score.toFixed(3)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Citations */}
                {message.citations && message.citations.length > 0 && (
                  <div className="mb-3">
                    <span className="font-medium text-gray-700">Citations:</span>
                    <div className="text-gray-600">
                      {message.citations.join(', ')}
                    </div>
                  </div>
                )}

                {/* Search Stats */}
                {message.search_stats && Object.keys(message.search_stats).length > 0 && (
                  <div className="mb-3">
                    <span className="font-medium text-gray-700">Search Stats:</span>
                    <div className="text-gray-600">
                      {message.search_stats.total_results && (
                        <div>Total results: {message.search_stats.total_results}</div>
                      )}
                      {message.search_stats.results_used && (
                        <div>Results used: {message.search_stats.results_used}</div>
                      )}
                      {message.search_stats.search_type && (
                        <div>Search type: {message.search_stats.search_type}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* RAG Details */}
                {message.rag_details && Object.keys(message.rag_details).length > 0 && (
                  <div>
                    <span className="font-medium text-gray-700">Processing Details:</span>
                    <div className="text-gray-600">
                      {message.rag_details.timestamp && (
                        <div>Processed: {new Date(message.rag_details.timestamp).toLocaleString()}</div>
                      )}
                      {message.rag_details.errors && message.rag_details.errors.length > 0 && (
                        <div className="text-red-600">
                          Errors: {message.rag_details.errors.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            </div>
          )}
        </>
      </div>
    </div>
  );  
};

export default MessageBubble;
