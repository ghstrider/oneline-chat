export interface ChatSummary {
  chat_id: string;
  chat_title?: string;
  last_message_preview: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  model_used?: string;
}

export interface ChatMessage {
  message_id: string;
  question: string;
  response: string;
  timestamp: string;
  mode: string;
  agents: any;
}

export interface ChatHistoryResponse {
  chat_id: string;
  chat_title?: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}