import { useState, useRef, useEffect } from 'react'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import ChatSettings from './ChatSettings'
import { ChatMessage, ChatMode, ChatSettings as ChatSettingsType } from '../types/chat'
import { streamChatMessageSSE, testConnection } from '../services/api'
import { useChatHistory } from '../contexts/ChatHistoryContext'

const ChatInterface = () => {
  const { currentChat, currentChatId, createNewChat } = useChatHistory()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [mode, setMode] = useState<ChatMode>('single')
  const [chatId, setChatId] = useState(() => `chat-${Date.now()}`)
  const [streamingContent, setStreamingContent] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [settings, setSettings] = useState<ChatSettingsType>({
    model: 'deepseek-r1:8b',
    temperature: 0.8,
    maxTokens: 200,
    saveToDb: true,
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // Load messages when switching to a different chat (not on every refresh)
  useEffect(() => {
    if (currentChat && currentChatId && chatId !== currentChatId) {
      // Only load if we're switching to a different chat
      // Convert chat history messages to ChatMessage format
      const historyMessages: ChatMessage[] = []
      
      currentChat.messages.forEach((msg) => {
        // Add user message
        if (msg.question) {
          historyMessages.push({
            id: `${msg.message_id}-user`,
            role: 'user',
            content: msg.question,
            timestamp: new Date(msg.timestamp),
          })
        }
        
        // Add assistant message
        if (msg.response) {
          historyMessages.push({
            id: `${msg.message_id}-assistant`,
            role: 'assistant',
            content: msg.response,
            timestamp: new Date(msg.timestamp),
          })
        }
      })
      
      setMessages(historyMessages)
      setChatId(currentChatId)
      setStreamingContent('')
    }
  }, [currentChat, currentChatId, chatId])

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setStreamingContent('')

    // Create placeholder for assistant message
    const assistantMessageId = `msg-${Date.now() + 1}`
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, assistantMessage])

    try {
      const fullContent = await streamChatMessageSSE(
        {
          message: content,
          chatId,
          mode,
          model: settings.model,
          temperature: settings.temperature,
          maxTokens: settings.maxTokens,
          saveToDb: settings.saveToDb,
        },
        // onChunk callback - update streaming content
        (chunk) => {
          setStreamingContent(prev => prev + chunk)
        },
        // onComplete callback
        () => {
          // Move streaming content to the actual message
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: streamingContent } 
                : msg
            )
          )
          setStreamingContent('')
          setIsLoading(false)
        },
        // onError callback
        (error) => {
          console.error('Streaming error:', error)
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: 'Sorry, I encountered an error. Please try again.' } 
                : msg
            )
          )
          setStreamingContent('')
          setIsLoading(false)
        }
      )

      // Update the assistant message with the full content
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: fullContent } 
            : msg
        )
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: 'Sorry, I encountered an error. Please try again.' } 
            : msg
        )
      )
    } finally {
      setIsLoading(false)
      setStreamingContent('')
    }
  }

  const handleClearChat = () => {
    setMessages([])
    setStreamingContent('')
    createNewChat()
    setChatId(`chat-${Date.now()}`)
  }

  const handleTestConnection = async () => {
    console.log('🔍 Testing connection...')
    try {
      const isConnected = await testConnection()
      if (isConnected) {
        alert('✅ Connection successful!')
      } else {
        alert('❌ Connection failed - check console for details')
      }
    } catch (error) {
      console.error('Connection test error:', error)
      alert('❌ Connection test failed - check console for details')
    }
  }

  // Get messages with streaming content
  const displayMessages = messages.map((msg, index) => {
    if (index === messages.length - 1 && msg.role === 'assistant' && streamingContent) {
      return { ...msg, content: streamingContent }
    }
    return msg
  })

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg h-[calc(100vh-12rem)]">
      <div className="flex flex-col h-full">
        {/* Chat Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              {currentChat && (
                <>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {currentChat.chat_title}
                  </h2>
                  <span className="text-sm text-gray-500 dark:text-gray-400">•</span>
                </>
              )}
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Mode:
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as ChatMode)}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="single">Single</option>
                <option value="multiple">Multiple</option>
              </select>
              
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Model: {settings.model}
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                API: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
              </span>
              
              <button
                onClick={handleTestConnection}
                className="px-3 py-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 border border-blue-300 dark:border-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                title="Test API Connection"
              >
                Test API
              </button>
              
              <div className="relative">
                <ChatSettings
                  settings={settings}
                  onSettingsChange={setSettings}
                  isOpen={settingsOpen}
                  onToggle={() => setSettingsOpen(!settingsOpen)}
                />
              </div>
              
              <button
                onClick={handleClearChat}
                className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors"
              >
                Clear Chat
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          <MessageList messages={displayMessages} />
          {isLoading && !streamingContent && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-3 max-w-[70%]">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  )
}

export default ChatInterface