import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import MessageList from './MessageList';
import { ChatMessage } from '../types/chat';
import { useAuth } from '../contexts/AuthContext';
import { getFullUrl } from '../config/api';

interface SharedChatData {
  share_token: string;
  chat_id: string;
  title: string;
  description?: string;
  is_public: boolean;
  view_count: number;
  created_at: string;
  messages: Array<{
    message_id: string;
    question: string;
    response: string;
    timestamp: string;
    mode: string;
    agents?: any;
  }>;
}

export const SharedChatViewer: React.FC = () => {
  const { shareToken } = useParams<{ shareToken: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [sharedChat, setSharedChat] = useState<SharedChatData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (shareToken) {
      loadSharedChat(shareToken);
    } else {
      setError('Invalid share token');
      setIsLoading(false);
    }
  }, [shareToken]);

  const loadSharedChat = async (token: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(getFullUrl(`/api/v1/shared/${token}`));
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('This shared chat was not found or has expired.');
        } else {
          setError('Failed to load shared chat.');
        }
        return;
      }

      const data: SharedChatData = await response.json();
      setSharedChat(data);
    } catch (error) {
      console.error('Error loading shared chat:', error);
      setError('Failed to load shared chat. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const convertToDisplayMessages = (messages: SharedChatData['messages']): ChatMessage[] => {
    const displayMessages: ChatMessage[] = [];
    
    messages.forEach((msg, index) => {
      // Add user message
      displayMessages.push({
        id: `${msg.message_id}-user`,
        role: 'user',
        content: msg.question,
        timestamp: new Date(msg.timestamp)
      });
      
      // Add assistant response
      displayMessages.push({
        id: `${msg.message_id}-assistant`,
        role: 'assistant',
        content: msg.response,
        timestamp: new Date(msg.timestamp)
      });
    });
    
    return displayMessages;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="text-lg text-gray-700 dark:text-gray-300">Loading shared chat...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md">
          <div className="text-center">
            <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Chat Not Found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {error}
            </p>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!sharedChat) {
    return null;
  }

  const displayMessages = convertToDisplayMessages(sharedChat.messages);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  {sharedChat.title}
                </h1>
                {sharedChat.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {sharedChat.description}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {!isAuthenticated && (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  <button
                    onClick={() => navigate('/')}
                    className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    Sign in
                  </button>
                  {' '}to start your own chat
                </div>
              )}
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {sharedChat.view_count} views
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-4xl mx-auto">
          <div className="p-6">
            {/* Chat Info */}
            <div className="mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                <span>Shared on {new Date(sharedChat.created_at).toLocaleDateString()}</span>
                <span>{sharedChat.messages.length} messages</span>
              </div>
            </div>

            {/* Messages */}
            <div className="space-y-4">
              {displayMessages.length > 0 ? (
                <MessageList messages={displayMessages} />
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400">
                    This shared chat has no messages.
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="mt-8 pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                This is a shared conversation from{' '}
                <button
                  onClick={() => navigate('/')}
                  className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                >
                  Oneline Chat
                </button>
              </p>
              {!isAuthenticated && (
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                  <button
                    onClick={() => navigate('/')}
                    className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    Create your own chat
                  </button>
                  {' '}to get started
                </p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};