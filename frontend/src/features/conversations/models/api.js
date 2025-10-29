/**
 * API service for conversations and messages
 */

import { Conversation, Message, ChatResponse } from './conversation.js';
import { API_BASE_URL } from '../../../config/api.js';

/**
 * Conversation API service
 */
export class ConversationAPI {
  /**
   * Get all conversations
   */
  static async getConversations() {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Conversation.fromAPIList(data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      throw error;
    }
  }

  /**
   * Get a specific conversation by ID
   */
  static async getConversation(id) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Conversation.fromAPI(data);
    } catch (error) {
      console.error('Error fetching conversation:', error);
      throw error;
    }
  }

  /**
   * Create a new conversation
   */
  static async createConversation(title = 'New Conversation') {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Conversation.fromAPI(data);
    } catch (error) {
      console.error('Error creating conversation:', error);
      throw error;
    }
  }

  /**
   * Update a conversation
   */
  static async updateConversation(id, updates) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Conversation.fromAPI(data);
    } catch (error) {
      console.error('Error updating conversation:', error);
      throw error;
    }
  }

  /**
   * Delete a conversation (soft delete)
   */
  static async deleteConversation(id) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return true;
    } catch (error) {
      console.error('Error deleting conversation:', error);
      throw error;
    }
  }

  /**
   * Get messages for a conversation
   */
  static async getMessages(conversationId) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.map(msg => Message.fromAPI(msg));
    } catch (error) {
      console.error('Error fetching messages:', error);
      throw error;
    }
  }

  /**
   * Send a chat message to a conversation
   */
  static async sendMessage(conversationId, message, retrieverType = 'hybrid_search') {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          retriever_type: retrieverType,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return ChatResponse.fromAPI(data);
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  /**
   * Add a message to a conversation (without chat processing)
   */
  static async addMessage(conversationId, messageData) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return Message.fromAPI(data);
    } catch (error) {
      console.error('Error adding message:', error);
      throw error;
    }
  }
}

/**
 * Chat API service (for standalone chat without conversations)
 */
export class ChatAPI {
  /**
   * Send a chat message (standalone)
   */
  static async sendMessage(message, retrieverType = 'hybrid_search') {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          retriever_type: retrieverType,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return ChatResponse.fromAPI(data);
    } catch (error) {
      console.error('Error sending chat message:', error);
      throw error;
    }
  }
}

export default ConversationAPI;
