/**
 * Conversation model and related types
 */

// Message types
export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system'
};

// Retriever types
export const RETRIEVER_TYPES = {
  HYBRID_SEARCH: 'hybrid_search',
  AGENTIC_RAG: 'agentic_rag'
};

// Response sources
export const RESPONSE_SOURCES = {
  HYBRID_SEARCH: 'hybrid_search',
  AGENTIC_RAG: 'agentic_rag',
  INTENT_DETECTION: 'intent_detection'
};

/**
 * Message model
 */
export class Message {
  constructor(data = {}) {
    this.id = data.id || null;
    this.conversation = data.conversation || null;
    this.content = data.content || '';
    this.message_type = data.message_type || MESSAGE_TYPES.USER;
    this.created_at = data.created_at || new Date().toISOString();
    
    // RAG response metadata
    this.retriever_type = data.retriever_type || null;
    this.source = data.source || null;
    this.confidence = data.confidence || null;
    this.sources = data.sources || [];
    this.citations = data.citations || [];
    this.search_stats = data.search_stats || {};
    this.rag_details = data.rag_details || {};
  }

  /**
   * Check if this is a user message
   */
  isUserMessage() {
    return this.message_type === MESSAGE_TYPES.USER;
  }

  /**
   * Check if this is an assistant message
   */
  isAssistantMessage() {
    return this.message_type === MESSAGE_TYPES.ASSISTANT;
  }

  /**
   * Check if this is a system message
   */
  isSystemMessage() {
    return this.message_type === MESSAGE_TYPES.SYSTEM;
  }

  /**
   * Get formatted timestamp
   */
  getFormattedTime() {
    const date = new Date(this.created_at);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * Get short content preview
   */
  getPreview(maxLength = 50) {
    if (this.content.length <= maxLength) {
      return this.content;
    }
    return this.content.substring(0, maxLength) + '...';
  }

  /**
   * Check if message has RAG metadata
   */
  hasRAGMetadata() {
    return this.retriever_type || this.sources.length > 0 || this.citations.length > 0;
  }

  /**
   * Get retriever type display name
   */
  getRetrieverTypeDisplay() {
    switch (this.retriever_type) {
      case RETRIEVER_TYPES.HYBRID_SEARCH:
        return 'Hybrid Search';
      case RETRIEVER_TYPES.AGENTIC_RAG:
        return 'Agentic RAG';
      default:
        return 'Unknown';
    }
  }

  /**
   * Get source display name
   */
  getSourceDisplay() {
    switch (this.source) {
      case RESPONSE_SOURCES.HYBRID_SEARCH:
        return 'Hybrid Search';
      case RESPONSE_SOURCES.AGENTIC_RAG:
        return 'Agentic RAG';
      case RESPONSE_SOURCES.INTENT_DETECTION:
        return 'Intent Detection';
      default:
        return 'Unknown';
    }
  }

  /**
   * Convert to API format
   */
  toAPI() {
    return {
      id: this.id,
      conversation: this.conversation,
      content: this.content,
      message_type: this.message_type,
      retriever_type: this.retriever_type,
      source: this.source,
      confidence: this.confidence,
      sources: this.sources,
      citations: this.citations,
      search_stats: this.search_stats,
      rag_details: this.rag_details
    };
  }

  /**
   * Create from API response
   */
  static fromAPI(data) {
    return new Message(data);
  }
}

/**
 * Conversation model
 */
export class Conversation {
  constructor(data = {}) {
    this.id = data.id || null;
    this.title = data.title || 'New Conversation';
    this.created_at = data.created_at || new Date().toISOString();
    this.updated_at = data.updated_at || new Date().toISOString();
    this.is_active = data.is_active !== false;
    this.message_count = data.message_count || 0;
    this.last_message = data.last_message || null;
    this.messages = data.messages ? data.messages.map(msg => Message.fromAPI(msg)) : [];
  }

  /**
   * Check if conversation is active
   */
  isActive() {
    return this.is_active;
  }

  /**
   * Get formatted creation date
   */
  getFormattedCreatedDate() {
    const date = new Date(this.created_at);
    return date.toLocaleDateString();
  }

  /**
   * Get formatted updated date
   */
  getFormattedUpdatedDate() {
    const date = new Date(this.updated_at);
    return date.toLocaleDateString();
  }

  /**
   * Get last message preview
   */
  getLastMessagePreview() {
    if (!this.last_message) {
      return 'No messages yet';
    }
    return this.last_message.content.length > 100 
      ? this.last_message.content.substring(0, 100) + '...'
      : this.last_message.content;
  }

  /**
   * Get last message time
   */
  getLastMessageTime() {
    if (!this.last_message) {
      return null;
    }
    return new Date(this.last_message.created_at).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }

  /**
   * Add a message to the conversation
   */
  addMessage(message) {
    if (message instanceof Message) {
      this.messages.push(message);
    } else {
      this.messages.push(Message.fromAPI(message));
    }
    this.message_count = this.messages.length;
    this.updated_at = new Date().toISOString();
  }

  /**
   * Get messages by type
   */
  getMessagesByType(messageType) {
    return this.messages.filter(msg => msg.message_type === messageType);
  }

  /**
   * Get user messages
   */
  getUserMessages() {
    return this.getMessagesByType(MESSAGE_TYPES.USER);
  }

  /**
   * Get assistant messages
   */
  getAssistantMessages() {
    return this.getMessagesByType(MESSAGE_TYPES.ASSISTANT);
  }

  /**
   * Check if conversation has messages
   */
  hasMessages() {
    return this.messages.length > 0;
  }

  /**
   * Get conversation summary
   */
  getSummary() {
    return {
      id: this.id,
      title: this.title,
      message_count: this.message_count,
      last_message_preview: this.getLastMessagePreview(),
      last_message_time: this.getLastMessageTime(),
      created_at: this.created_at,
      updated_at: this.updated_at
    };
  }

  /**
   * Convert to API format
   */
  toAPI() {
    return {
      id: this.id,
      title: this.title,
      is_active: this.is_active
    };
  }

  /**
   * Create from API response
   */
  static fromAPI(data) {
    return new Conversation(data);
  }

  /**
   * Create list from API response
   */
  static fromAPIList(dataArray) {
    return dataArray.map(data => Conversation.fromAPI(data));
  }
}

/**
 * Chat response model
 */
export class ChatResponse {
  constructor(data = {}) {
    this.type = data.type || 'text';
    this.text = data.text || '';
    this.actionType = data.actionType || null;
    this.widget = data.widget || null;
    this.title = data.title || null;
    this.fields = data.fields || [];
    this.source = data.source || null;
    this.retriever_type = data.retriever_type || null;
    this.confidence = data.confidence || null;
    this.citations = data.citations || [];
    this.sources_used = data.sources_used || [];
    this.rag_details = data.rag_details || {};
    this.sources = data.sources || [];
    this.search_stats = data.search_stats || {};
    this.message_id = data.message_id || null;
  }

  /**
   * Check if response has text
   */
  hasText() {
    return this.text && this.text.trim().length > 0;
  }

  /**
   * Check if response has action
   */
  hasAction() {
    return this.actionType && this.widget;
  }

  /**
   * Check if response has RAG metadata
   */
  hasRAGMetadata() {
    return this.retriever_type || this.sources.length > 0 || this.citations.length > 0;
  }

  /**
   * Get source display name
   */
  getSourceDisplay() {
    switch (this.source) {
      case RESPONSE_SOURCES.HYBRID_SEARCH:
        return 'Hybrid Search';
      case RESPONSE_SOURCES.AGENTIC_RAG:
        return 'Agentic RAG';
      case RESPONSE_SOURCES.INTENT_DETECTION:
        return 'Intent Detection';
      default:
        return 'Unknown';
    }
  }

  /**
   * Get retriever type display name
   */
  getRetrieverTypeDisplay() {
    switch (this.retriever_type) {
      case RETRIEVER_TYPES.HYBRID_SEARCH:
        return 'Hybrid Search';
      case RETRIEVER_TYPES.AGENTIC_RAG:
        return 'Agentic RAG';
      default:
        return 'Unknown';
    }
  }

  /**
   * Convert to Message object
   */
  toMessage(conversationId, messageType = MESSAGE_TYPES.ASSISTANT) {
    return new Message({
      conversation: conversationId,
      content: this.text,
      message_type: messageType,
      retriever_type: this.retriever_type,
      source: this.source,
      confidence: this.confidence,
      sources: this.sources || this.sources_used || [],
      citations: this.citations,
      search_stats: this.search_stats,
      rag_details: this.rag_details
    });
  }

  /**
   * Create from API response
   */
  static fromAPI(data) {
    return new ChatResponse(data);
  }
}
