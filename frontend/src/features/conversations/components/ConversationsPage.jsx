import React, { useState, useEffect } from 'react';
import { ConversationAPI } from '../models/api.js';
import { Conversation, Message, MESSAGE_TYPES, RETRIEVER_TYPES } from '../models/conversation.js';
import ConversationSidebar from './ConversationSidebar.jsx';
import ConversationChat from './ConversationChat.jsx';
import { Plus, MessageSquare } from 'lucide-react';

const ConversationsPage = () => {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load conversations on component mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load messages when conversation changes
  useEffect(() => {
    if (currentConversation) {
      loadMessages(currentConversation.id);
    } else {
      setMessages([]);
    }
  }, [currentConversation]);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedConversations = await ConversationAPI.getConversations();
      setConversations(fetchedConversations);
    } catch (err) {
      console.error('Error loading conversations:', err);
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId) => {
    try {
      setLoading(true);
      setError(null);
      const fetchedMessages = await ConversationAPI.getMessages(conversationId);
      setMessages(fetchedMessages);
    } catch (err) {
      console.error('Error loading messages:', err);
      setError('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const createNewConversation = async () => {
    try {
      setLoading(true);
      setError(null);
      const newConversation = await ConversationAPI.createConversation();
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversation(newConversation);
    } catch (err) {
      console.error('Error creating conversation:', err);
      setError('Failed to create conversation');
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = async (conversation) => {
    setCurrentConversation(conversation);
  };

  const deleteConversation = async (conversationId) => {
    try {
      await ConversationAPI.deleteConversation(conversationId);
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      // If the deleted conversation was currently selected, clear selection
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
      setError('Failed to delete conversation');
    }
  };

  const updateConversationTitle = async (conversationId, newTitle) => {
    try {
      const updatedConversation = await ConversationAPI.updateConversation(conversationId, {
        title: newTitle
      });
      setConversations(prev => 
        prev.map(conv => conv.id === conversationId ? updatedConversation : conv)
      );
      
      // Update current conversation if it's the one being updated
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation(updatedConversation);
      }
    } catch (err) {
      console.error('Error updating conversation title:', err);
      setError('Failed to update conversation title');
    }
  };

  const sendMessage = async (messageContent, retrieverType = RETRIEVER_TYPES.HYBRID_SEARCH) => {
    if (!currentConversation || !messageContent.trim()) {
      return;
    }

    try {
      // Add user message immediately to UI
      const userMessage = new Message({
        conversation: currentConversation.id,
        content: messageContent,
        message_type: MESSAGE_TYPES.USER,
        created_at: new Date().toISOString()
      });
      setMessages(prev => [...prev, userMessage]);

      // Send message to API
      const response = await ConversationAPI.sendMessage(
        currentConversation.id,
        messageContent,
        retrieverType
      );

      // Add assistant response to UI
      const assistantMessage = response.toMessage(currentConversation.id, MESSAGE_TYPES.ASSISTANT);
      assistantMessage.id = response.message_id; // Use the ID from the response
      setMessages(prev => [...prev, assistantMessage]);

      // Update conversations list to show new last message
      await loadConversations();
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message');
      
      // Remove the user message if sending failed
      setMessages(prev => prev.filter(msg => msg.id !== null || msg.content !== messageContent));
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <ConversationSidebar
          conversations={conversations}
          currentConversation={currentConversation}
          loading={loading}
          error={error}
          onSelectConversation={selectConversation}
          onDeleteConversation={deleteConversation}
          onUpdateTitle={updateConversationTitle}
          onCreateNew={createNewConversation}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentConversation ? (
          <ConversationChat
            conversation={currentConversation}
            messages={messages}
            loading={loading}
            error={error}
            onSendMessage={sendMessage}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Welcome to Conversations
              </h3>
              <p className="text-gray-500 mb-4">
                Select a conversation from the sidebar or create a new one to start chatting.
              </p>
              <button
                onClick={createNewConversation}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <Plus className="h-4 w-4 mr-2" />
                {loading ? 'Creating...' : 'New Conversation'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationsPage;
