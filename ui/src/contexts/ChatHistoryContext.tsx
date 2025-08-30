import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { chatHistoryApi } from '../services/chat-history';
import { ChatSummary, ChatHistoryResponse } from '../types/chat-history';

interface ChatHistoryState {
  chats: ChatSummary[];
  currentChatId: string | null;
  currentChat: ChatHistoryResponse | null;
  loading: boolean;
  searchQuery: string;
  refreshChats: () => Promise<void>;
  loadChat: (chatId: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
  updateChatTitle: (chatId: string, title: string) => Promise<void>;
  searchChats: (query: string) => void;
  createNewChat: () => void;
}

const ChatHistoryContext = createContext<ChatHistoryState | undefined>(undefined);

export const useChatHistory = () => {
  const context = useContext(ChatHistoryContext);
  if (!context) {
    throw new Error('useChatHistory must be used within a ChatHistoryProvider');
  }
  return context;
};

interface ChatHistoryProviderProps {
  children: ReactNode;
}

export const ChatHistoryProvider: React.FC<ChatHistoryProviderProps> = ({ children }) => {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [currentChat, setCurrentChat] = useState<ChatHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Load all chats on mount
  useEffect(() => {
    refreshChats();
  }, []);

  const refreshChats = async () => {
    setLoading(true);
    try {
      const allChats = await chatHistoryApi.getAllChats(50, 0, searchQuery || undefined);
      setChats(allChats);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadChat = async (chatId: string) => {
    setLoading(true);
    try {
      const chatHistory = await chatHistoryApi.getFullChatHistory(chatId);
      setCurrentChat(chatHistory);
      setCurrentChatId(chatId);
    } catch (error) {
      console.error('Failed to load chat:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteChat = async (chatId: string) => {
    try {
      await chatHistoryApi.deleteChat(chatId);
      
      // Remove from local state
      setChats(chats.filter(chat => chat.chat_id !== chatId));
      
      // If the deleted chat is current, clear it
      if (currentChatId === chatId) {
        setCurrentChatId(null);
        setCurrentChat(null);
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      throw error;
    }
  };

  const updateChatTitle = async (chatId: string, title: string) => {
    try {
      await chatHistoryApi.updateChatTitle(chatId, title);
      
      // Update local state
      setChats(chats.map(chat => 
        chat.chat_id === chatId ? { ...chat, chat_title: title } : chat
      ));
      
      // Update current chat if it's the one being updated
      if (currentChat && currentChat.chat_id === chatId) {
        setCurrentChat({ ...currentChat, chat_title: title });
      }
    } catch (error) {
      console.error('Failed to update chat title:', error);
      throw error;
    }
  };

  const searchChats = (query: string) => {
    setSearchQuery(query);
  };

  // Trigger search when query changes
  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      refreshChats();
    }, 300); // Debounce search

    return () => clearTimeout(delayedSearch);
  }, [searchQuery]);

  const createNewChat = () => {
    setCurrentChatId(null);
    setCurrentChat(null);
  };

  const value: ChatHistoryState = {
    chats,
    currentChatId,
    currentChat,
    loading,
    searchQuery,
    refreshChats,
    loadChat,
    deleteChat,
    updateChatTitle,
    searchChats,
    createNewChat
  };

  return (
    <ChatHistoryContext.Provider value={value}>
      {children}
    </ChatHistoryContext.Provider>
  );
};