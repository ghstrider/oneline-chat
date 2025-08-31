import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatHistory } from '../../contexts/ChatHistoryContext';
import { ChatSummary } from '../../types/chat-history';

interface ChatHistoryItemProps {
  chat: ChatSummary;
  isActive: boolean;
}

export const ChatHistoryItem: React.FC<ChatHistoryItemProps> = ({ chat, isActive }) => {
  const { loadChat, deleteChat, updateChatTitle } = useChatHistory();
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(chat.chat_title || '');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleClick = () => {
    if (!isEditing) {
      // Update URL and load chat
      navigate(`/chat/${chat.chat_id}`);
      loadChat(chat.chat_id);
    }
  };

  const handleRename = async () => {
    if (editTitle.trim() && editTitle !== chat.chat_title) {
      try {
        await updateChatTitle(chat.chat_id, editTitle.trim());
      } catch (error) {
        console.error('Failed to update title:', error);
        setEditTitle(chat.chat_title || '');
      }
    }
    setIsEditing(false);
    setShowMenu(false);
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this chat?')) {
      setIsDeleting(true);
      try {
        await deleteChat(chat.chat_id);
      } catch (error) {
        console.error('Failed to delete chat:', error);
        setIsDeleting(false);
      }
    }
    setShowMenu(false);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 1 week
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  if (isDeleting) {
    return (
      <div className="p-4 opacity-50">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-500"></div>
          <span className="text-sm text-gray-500">Deleting...</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`group relative p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
        isActive ? 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-blue-500' : ''
      }`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onBlur={handleRename}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRename();
                if (e.key === 'Escape') {
                  setIsEditing(false);
                  setEditTitle(chat.chat_title || '');
                }
              }}
              className="w-full p-1 text-sm font-medium bg-white dark:bg-gray-700 border border-blue-500 rounded"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {chat.chat_title || 'Untitled Chat'}
            </h3>
          )}
          
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-1">
            {chat.last_message_preview}
          </p>
          
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {formatTimestamp(chat.updated_at)}
            </span>
            <div className="flex items-center space-x-2">
              {chat.model_used && (
                <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">
                  {chat.model_used}
                </span>
              )}
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {chat.message_count} msg{chat.message_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </div>

        {/* Menu Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-opacity"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01" />
          </svg>
        </button>

        {/* Context Menu */}
        {showMenu && (
          <div className="absolute right-4 top-12 w-40 bg-white dark:bg-gray-700 rounded-md shadow-lg z-50 py-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
                setShowMenu(false);
              }}
              className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              Rename
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDelete();
              }}
              className="block w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Click outside to close menu */}
      {showMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  );
};