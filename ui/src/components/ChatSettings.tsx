import { ChatSettings as ChatSettingsType } from '../types/chat'

interface ChatSettingsProps {
  settings: ChatSettingsType
  onSettingsChange: (settings: ChatSettingsType) => void
  isOpen: boolean
  onToggle: () => void
}

const ChatSettings = ({ settings, onSettingsChange, isOpen, onToggle }: ChatSettingsProps) => {
  const handleModelChange = (model: string) => {
    onSettingsChange({ ...settings, model })
  }

  const handleTemperatureChange = (temperature: number) => {
    onSettingsChange({ ...settings, temperature })
  }

  const handleMaxTokensChange = (maxTokens: number) => {
    onSettingsChange({ ...settings, maxTokens })
  }

  const handleSaveToDbChange = (saveToDb: boolean) => {
    onSettingsChange({ ...settings, saveToDb })
  }

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        title="Chat Settings"
      >
        ⚙️
      </button>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 min-w-80">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Chat Settings
        </h3>
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Model
          </label>
          <select
            value={settings.model}
            onChange={(e) => handleModelChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="deepseek-r1:8b">DeepSeek R1 8B</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="gpt-4">GPT-4</option>
            <option value="claude-3-haiku">Claude 3 Haiku</option>
            <option value="claude-3-sonnet">Claude 3 Sonnet</option>
          </select>
        </div>

        {/* Temperature */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Temperature: {settings.temperature}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={settings.temperature}
            onChange={(e) => handleTemperatureChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>Conservative</span>
            <span>Creative</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Max Tokens
          </label>
          <input
            type="number"
            min="50"
            max="4000"
            step="50"
            value={settings.maxTokens}
            onChange={(e) => handleMaxTokensChange(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Save to DB */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="saveToDb"
            checked={settings.saveToDb}
            onChange={(e) => handleSaveToDbChange(e.target.checked)}
            className="h-4 w-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
          />
          <label htmlFor="saveToDb" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
            Save conversations to database
          </label>
        </div>
      </div>
    </div>
  )
}

export default ChatSettings