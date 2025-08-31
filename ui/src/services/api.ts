import { ChatRequest, ChatResponse, ApiChatRequest } from '../types/chat'
import { API_CONFIG } from '../config/api'
import apiClient from '../config/axios'

export async function sendChatMessage(request: ChatRequest & { agentId?: string }): Promise<ChatResponse> {
  const apiRequest: ApiChatRequest & { agent_id?: string } = {
    model: request.model || 'deepseek-r1:8b',
    messages: [
      {
        role: 'user',
        content: request.message,
      },
    ],
    stream: false,
    temperature: request.temperature || 0.8,
    max_tokens: request.maxTokens || 200,
    chat_id: request.chatId,
    save_to_db: request.saveToDb ?? true,
    agent_id: request.agentId,
  }

  console.log('🚀 Sending chat request:', {
    url: `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chat}`,
    method: 'POST',
    payload: apiRequest
  })

  try {
    const response = await apiClient.post(API_CONFIG.endpoints.chat, apiRequest)
    console.log('✅ Chat response received:', response)
    
    return {
      messageId: response.data.id,
      content: response.data.choices[0].message.content,
      chatId: request.chatId,
      mode: request.mode,
    }
  } catch (error) {
    console.error('❌ Chat API Error:', error)
    throw error
  }
}

export async function streamChatMessage(
  request: ChatRequest & { agentId?: string },
  onChunk: (chunk: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void
): Promise<string> {
  let fullContent = ''
  
  try {
    const apiRequest: ApiChatRequest & { agent_id?: string } = {
      model: request.model || 'deepseek-r1:8b',
      messages: [
        {
          role: 'user',
          content: request.message,
        },
      ],
      stream: true,
      temperature: request.temperature || 0.8,
      max_tokens: request.maxTokens || 200,
      chat_id: request.chatId,
      save_to_db: request.saveToDb ?? true,
      agent_id: request.agentId,
    }

    console.log('🚀 Starting stream request:', {
      url: `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stream}`,
      method: 'POST',
      payload: apiRequest
    })

    // Use axios for streaming with responseType: 'stream'
    const response = await apiClient.post(API_CONFIG.endpoints.stream, apiRequest, {
      responseType: 'stream',
      headers: {
        'Accept': 'text/event-stream',
      },
    })

    console.log('✅ Stream response started:', response.status)

    const reader = response.data.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('Response body is not readable')
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          
          if (data === '[DONE]') {
            console.log('🏁 Stream completed')
            onComplete?.()
            return fullContent
          }
          
          if (data) {
            try {
              const parsed = JSON.parse(data)
              const content = parsed.choices?.[0]?.delta?.content || ''
              if (content) {
                fullContent += content
                onChunk(content)
              }
            } catch (e) {
              console.error('Failed to parse chunk:', e, 'Data:', data)
            }
          }
        }
      }
    }
    
    onComplete?.()
    return fullContent
  } catch (error) {
    console.error('❌ Stream error:', error)
    const err = error instanceof Error ? error : new Error('Unknown error occurred')
    onError?.(err)
    throw err
  }
}

// Alternative streaming implementation using fetch for better SSE support
export async function streamChatMessageSSE(
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void
): Promise<string> {
  let fullContent = ''
  
  try {
    const apiRequest: ApiChatRequest = {
      model: request.model || 'deepseek-r1:8b',
      messages: [
        {
          role: 'user',
          content: request.message,
        },
      ],
      stream: true,
      temperature: request.temperature || 0.8,
      max_tokens: request.maxTokens || 200,
      chat_id: request.chatId,
      save_to_db: request.saveToDb ?? true,
    }

    const url = `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stream}`
    console.log('🚀 Starting SSE stream:', {
      url,
      method: 'POST',
      payload: apiRequest
    })

    // Get authentication token if available
    const token = localStorage.getItem('sessionToken')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    // Use fetch for SSE streaming (better browser support)
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(apiRequest),
    })

    console.log('📡 SSE Response:', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries())
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('Response body is not readable')
    }

    let chunkCount = 0
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        console.log(`🏁 Stream ended after ${chunkCount} chunks`)
        break
      }

      chunkCount++
      const chunk = decoder.decode(value)
      console.log(`📦 Chunk ${chunkCount}:`, chunk.substring(0, 100) + '...')
      
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          
          if (data === '[DONE]') {
            console.log('🏁 Stream completed with [DONE]')
            onComplete?.()
            return fullContent
          }
          
          if (data) {
            try {
              const parsed = JSON.parse(data)
              const content = parsed.choices?.[0]?.delta?.content || ''
              if (content) {
                fullContent += content
                onChunk(content)
              }
            } catch (e) {
              console.error('Failed to parse chunk:', e, 'Data:', data)
            }
          }
        }
      }
    }
    
    console.log('✅ Stream completed, total content length:', fullContent.length)
    onComplete?.()
    return fullContent
  } catch (error) {
    console.error('❌ SSE Stream error:', error)
    const err = error instanceof Error ? error : new Error('Unknown error occurred')
    onError?.(err)
    throw err
  }
}

export async function getChatHistory(chatId: string): Promise<any> {
  console.log('🚀 Getting chat history for:', chatId)
  
  try {
    const response = await apiClient.get(`${API_CONFIG.endpoints.history}/${chatId}`)
    console.log('✅ Chat history response:', response)
    return response.data
  } catch (error) {
    console.error('❌ Get Chat History Error:', error)
    throw error
  }
}

export async function getAvailableModels(): Promise<any> {
  console.log('🚀 Getting available models')
  
  try {
    const response = await apiClient.get(API_CONFIG.endpoints.models)
    console.log('✅ Models response:', response)
    return response.data
  } catch (error) {
    console.error('❌ Get Models Error:', error)
    throw error
  }
}

// Test function to check connectivity
export async function testConnection(): Promise<boolean> {
  console.log('🔍 Testing API connection to:', API_CONFIG.baseUrl)
  
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    })
    
    console.log('🔍 Health check response:', {
      status: response.status,
      statusText: response.statusText,
      url: response.url
    })
    
    return response.ok
  } catch (error) {
    console.error('❌ Connection test failed:', error)
    return false
  }
}