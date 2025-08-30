import React, { useState, useEffect } from 'react';
import { useChatHistory } from '../../contexts/ChatHistoryContext';
import { ChatHistoryItem } from './ChatHistoryItem';
import { ChatSearchBar } from './ChatSearchBar';

interface ChatHistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isMobile?: boolean;
}

export const ChatHistoryPanel: React.FC<ChatHistoryPanelProps> = ({ isOpen, onClose, isMobile }) => {
  const { chats, loading, createNewChat, currentChatId } = useChatHistory();
  const [isMobileView, setIsMobileView] = useState(false);

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobileView(isMobile || window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [isMobile]);

  if (!isOpen) return null;

  const sidebarContent = (
    <>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Chat History
        </h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={createNewChat}
            className="p-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            title="New Chat"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          {isMobileView && (
            <button
              onClick={onClose}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <ChatSearchBar />
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : chats.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500 dark:text-gray-400">
              No chat history found
            </p>
            <button
              onClick={createNewChat}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Start New Chat
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {chats.map((chat) => (
              <ChatHistoryItem
                key={chat.chat_id}
                chat={chat}
                isActive={currentChatId === chat.chat_id}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );

  if (isMobileView) {
    // Mobile overlay mode
    return (
      <div className="fixed inset-0 z-50 flex">
        {/* Overlay */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50"
          onClick={onClose}
        />
        
        {/* Sidebar */}
        <div className="relative flex flex-col w-80 max-w-xs bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-full">
          {sidebarContent}
        </div>
      </div>
    );
  } else {
    // Desktop integrated mode
    return (
      <div className="flex flex-col w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-full">
        {sidebarContent}
      </div>
    );
  }
};