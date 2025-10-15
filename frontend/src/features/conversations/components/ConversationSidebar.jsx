import React, { useState } from 'react';
import { 
  Plus, 
  Trash2, 
  Pencil,
  Check,
  X,
  MessageSquare
} from 'lucide-react';

const ConversationSidebar = ({
  conversations,
  currentConversation,
  loading,
  error,
  onSelectConversation,
  onDeleteConversation,
  onUpdateTitle,
  onCreateNew
}) => {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const handleEditStart = (conversation) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleEditSave = async (conversationId) => {
    if (editTitle.trim()) {
      await onUpdateTitle(conversationId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handleKeyPress = (e, conversationId) => {
    if (e.key === 'Enter') {
      handleEditSave(conversationId);
    } else if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const handleDelete = async (e, conversationId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      await onDeleteConversation(conversationId);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <button
            onClick={onCreateNew}
            disabled={loading}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
            title="New Conversation"
          >
            <Plus className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-4 mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {loading && conversations.length === 0 ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Loading conversations...</p>
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center">
            <MessageSquare className="mx-auto h-8 w-8 text-gray-400 mb-2" />
            <p className="text-sm text-gray-500">No conversations yet</p>
            <button
              onClick={onCreateNew}
              className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Create your first conversation
            </button>
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onSelectConversation(conversation)}
                className={`group relative p-3 mb-2 rounded-lg cursor-pointer transition-colors ${
                  currentConversation?.id === conversation.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {/* Title */}
                    {editingId === conversation.id ? (
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => handleKeyPress(e, conversation.id)}
                        onBlur={() => handleEditSave(conversation.id)}
                        className="w-full text-sm font-medium text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        autoFocus
                      />
                    ) : (
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {conversation.title}
                      </h3>
                    )}

                    {/* Last Message Preview */}
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                      {conversation.getLastMessagePreview()}
                    </p>

                    {/* Metadata */}
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-400">
                        {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''}
                      </span>
                      <span className="text-xs text-gray-400">
                        {conversation.getLastMessageTime()}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {editingId === conversation.id ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditSave(conversation.id);
                          }}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                          title="Save"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditCancel();
                          }}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="Cancel"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditStart(conversation);
                          }}
                          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                          title="Edit title"
                        >
                          <Pencil className="h-3 w-3" />
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, conversation.id)}
                          className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Delete conversation"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
};

export default ConversationSidebar;
