import { ChatMessage } from '../types/chat'

interface MessageProps {
  message: ChatMessage & {
    agentName?: string
    agentAvatar?: string
    agentModel?: string
  }
}

const Message = ({ message }: MessageProps) => {
  const isUser = message.role === 'user'

  const getAgentDisplay = () => {
    if (message.agentName) {
      return {
        name: message.agentName,
        avatar: message.agentAvatar || '🤖',
        model: message.agentModel
      }
    }
    return {
      name: 'Assistant',
      avatar: '🤖',
      model: undefined
    }
  }

  const agentDisplay = getAgentDisplay()

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`
          max-w-[70%] rounded-lg px-4 py-3
          ${isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
          }
        `}
      >
        <div className="flex items-center space-x-2 text-sm font-semibold mb-1">
          {isUser ? (
            <span>You</span>
          ) : (
            <>
              <span className="text-lg">{agentDisplay.avatar}</span>
              <span>{agentDisplay.name}</span>
              {agentDisplay.model && (
                <span className="text-xs opacity-70 font-normal">
                  • {agentDisplay.model}
                </span>
              )}
            </>
          )}
        </div>
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>
        <div className="text-xs mt-2 opacity-70">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

export default Message