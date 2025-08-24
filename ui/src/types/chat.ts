export type ChatRole = 'user' | 'assistant'
export type ChatMode = 'single' | 'multiple'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: Date
}

export interface ChatRequest {
  message: string
  chatId: string
  mode: ChatMode
  model?: string
  temperature?: number
  maxTokens?: number
  saveToDb?: boolean
}

export interface ChatResponse {
  messageId: string
  content: string
  chatId: string
  mode: ChatMode
}

export interface ApiChatRequest {
  model: string
  messages: Array<{
    role: ChatRole
    content: string
  }>
  stream: boolean
  temperature?: number
  max_tokens?: number
  chat_id: string
  save_to_db?: boolean
}

export interface ChatSettings {
  model: string
  temperature: number
  maxTokens: number
  saveToDb: boolean
}