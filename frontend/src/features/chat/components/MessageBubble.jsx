import React from 'react'
import MarkdownWidget from '../../core/components/MarkdownWidget'

function MessageBubble({ role, children, ragDetails, onShowRAGDetails }) {
  const isUser = role === 'user'
  const hasRAGDetails = ragDetails && ragDetails.confidence !== undefined
  
  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${isUser ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-gray-100 text-gray-900 rounded-bl-sm'}`}>
        <MarkdownWidget content={children} isUser={isUser} />
        {hasRAGDetails && (
          <div className="mt-2 flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs opacity-75">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>Confidence: {Math.round(ragDetails.confidence * 100)}%</span>
            </div>
            <button
              onClick={() => onShowRAGDetails(ragDetails)}
              className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600 transition-colors"
              title="View RAG Details"
            >
              📊 Details
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
