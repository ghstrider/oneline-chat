import { useState, KeyboardEvent } from 'react'
import AgentTriggerButton from './agents/AgentTriggerButton'
import AgentModal from './agents/AgentModal'
import { useAgentSelection } from '../hooks/useAgentSelection'
import { Agent } from '../hooks/useAgents'

interface MessageInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  chatId?: string | null
}

const MessageInput = ({ onSendMessage, disabled, chatId }: MessageInputProps) => {
  const [input, setInput] = useState('')
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false)
  const { activeAgent, loading: agentLoading } = useAgentSelection(chatId)

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input)
      setInput('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleAgentSelected = (agent: Agent) => {
    console.log('Agent selected:', agent.name)
  }

  return (
    <>
      <div className="flex flex-col space-y-3">
        {/* Agent Selection Row */}
        <div className="flex items-center justify-between">
          <AgentTriggerButton
            activeAgent={activeAgent}
            onClick={() => setIsAgentModalOpen(true)}
            loading={agentLoading}
          />
          
          {activeAgent && (
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Ready to chat with {activeAgent.name}
            </div>
          )}
        </div>

        {/* Input Row */}
        <div className="flex space-x-4">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={disabled}
            className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={2}
          />
          <button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            className={`
              px-6 py-3 rounded-lg font-medium transition-colors
              ${disabled || !input.trim()
                ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
              }
            `}
          >
            Send
          </button>
        </div>
      </div>

      {/* Agent Selection Modal */}
      <AgentModal
        isOpen={isAgentModalOpen}
        onClose={() => setIsAgentModalOpen(false)}
        chatId={chatId}
        onAgentSelected={handleAgentSelected}
      />
    </>
  )
}

export default MessageInput