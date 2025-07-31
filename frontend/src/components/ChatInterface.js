import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { chatAPI } from '../services/api';

const ChatInterface = ({ invoices = [], sessionId = null }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !sessionId) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    
    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }]);

    try {
      // Call the chat API
      console.log(`💬 Sending chat message to session ${sessionId}`);
      const response = await chatAPI.sendMessage(sessionId, userMessage);
      
      if (response.success) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'assistant',
          content: response.response,
          timestamp: new Date()
        }]);
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="group flex items-center space-x-3 bg-white rounded-full shadow-lg border-2 border-transparent bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-0.5 hover:shadow-xl transition-all duration-300"
        >
          <div className="bg-white rounded-full px-4 py-3 flex items-center space-x-2">
            <MessageCircle className="h-5 w-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Ask about invoices</span>
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-0.5 rounded-lg shadow-2xl w-full max-w-2xl h-[600px]">
        <div className="bg-white rounded-lg h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Invoice Analysis</h3>
              <p className="text-sm text-gray-500">
                {invoices.length} documents loaded
                {sessionId && <span className="ml-2 text-green-600">• Chat Ready</span>}
                {!sessionId && <span className="ml-2 text-yellow-600">• Session Loading...</span>}
              </p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-8">
                <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-sm">Ask questions about your uploaded invoices</p>
                <div className="mt-4 text-xs text-gray-400 space-y-1">
                  <p>"What's the total amount across all invoices?"</p>
                  <p>"Which vendor charged the most?"</p>
                  <p>"How many invoices have Net 30 terms?"</p>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={sessionId ? "Ask about your invoices..." : "Setting up chat session..."}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                disabled={isLoading || !sessionId}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isLoading || !sessionId}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg transition-colors duration-200 flex items-center"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 