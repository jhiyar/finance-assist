import React from 'react';
import { Send } from 'lucide-react';

const ChatInput = ({
  value,
  onChange,
  onSubmit,
  onKeyPress,
  placeholder = "Type your message here...",
  disabled = false,
  loading = false
}) => {
  return (
    <div className="flex items-end space-x-3">
      <div className="flex-1">
        <textarea
          value={value}
          onChange={onChange}
          onKeyPress={onKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
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
        />
      </div>
      <button
        onClick={onSubmit}
        disabled={!value.trim() || disabled || loading}
        className="p-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
        ) : (
          <Send className="h-5 w-5" />
        )}
      </button>
    </div>
  );
};

export default ChatInput;
