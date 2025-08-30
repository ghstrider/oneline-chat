import { api } from '../config/axios';
import { ChatSummary, ChatHistoryResponse } from '../types/chat-history';

export const chatHistoryApi = {
  // Get all chat summaries
  getAllChats: async (
    limit: number = 50,
    offset: number = 0,
    search?: string
  ): Promise<ChatSummary[]> => {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
      ...(search && { search })
    });
    
    const response = await api.get<ChatSummary[]>(`/api/v1/chats?${params}`);
    return response.data;
  },

  // Get full chat history with all messages
  getFullChatHistory: async (chatId: string): Promise<ChatHistoryResponse> => {
    const response = await api.get<ChatHistoryResponse>(`/api/v1/chat/${chatId}/full`);
    return response.data;
  },

  // Delete a chat
  deleteChat: async (chatId: string): Promise<void> => {
    await api.delete(`/api/v1/chat/${chatId}`);
  },

  // Update chat title
  updateChatTitle: async (chatId: string, title: string): Promise<void> => {
    await api.put(`/api/v1/chat/${chatId}/title`, { title });
  },

  // Get chat summary
  getChatSummary: async (chatId: string): Promise<ChatSummary> => {
    const response = await api.get<ChatSummary>(`/api/v1/chat/${chatId}/summary`);
    return response.data;
  }
};