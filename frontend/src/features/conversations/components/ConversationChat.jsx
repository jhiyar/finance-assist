import React, { useState, useRef, useEffect } from 'react';
import { ConversationAPI } from '../models/api.js';
import { Message, MESSAGE_TYPES, RETRIEVER_TYPES } from '../models/conversation.js';
import MessageBubble from './MessageBubble.jsx';
import ChatInput from './ChatInput.jsx';
import { 
  Send,
  MessageSquare,
  AlertTriangle
} from 'lucide-react';

const ConversationChat = ({
  conversation,
  messages,
  loading,
  error,
  onSendMessage
}) => {
  const [newMessage, setNewMessage] = useState('');
  const [retrieverType, setRetrieverType] = useState(RETRIEVER_TYPES.HYBRID_SEARCH);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when conversation changes
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [conversation]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim() || sending) {
      return;
    }

    const messageContent = newMessage.trim();
    setNewMessage('');
    setSending(true);

    try {
      await onSendMessage(messageContent, retrieverType);
    } catch (err) {
      console.error('Error sending message:', err);
      // Restore message if sending failed
      setNewMessage(messageContent);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const handleRetrieverTypeChange = (e) => {
    setRetrieverType(e.target.value);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {conversation.title}
            </h2>
            <p className="text-sm text-gray-500">
              Created {conversation.getFormattedCreatedDate()}
              {conversation.message_count > 0 && (
                <span> • {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''}</span>
              )}
            </p>
          </div>
          
          {/* Retriever Type Selector */}
          <div className="flex items-center space-x-2">
            <label htmlFor="retriever-type" className="text-sm font-medium text-gray-700">
              Search:
            </label>
            <select
              id="retriever-type"
              value={retrieverType}
              onChange={handleRetrieverTypeChange}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={RETRIEVER_TYPES.HYBRID_SEARCH}>Hybrid Search</option>
              <option value={RETRIEVER_TYPES.AGENTIC_RAG}>Agentic RAG</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-4 mt-2 p-3 bg-red-50 border border-red-200 rounded-md flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <MessageSquare className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Start a conversation
              </h3>
              <p className="text-gray-500">
                Send your first message to begin chatting with the AI assistant.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble
                key={message.id || index}
                message={message}
                showTimestamp={true}
              />
            ))}
            
            {/* Loading indicator for new messages */}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-xs">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSendMessage} className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={1}
              style={{
                minHeight: '40px',
                maxHeight: '120px',
                height: 'auto'
              }}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              disabled={sending}
            />
          </div>
          <button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="p-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
        
        {/* Input Help Text */}
        <div className="mt-2 text-xs text-gray-500">
          <span>Using {retrieverType === RETRIEVER_TYPES.HYBRID_SEARCH ? 'Hybrid Search' : 'Agentic RAG'}</span>
          <span className="mx-2">•</span>
          <span>Press Enter to send, Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};

export default ConversationChat;
