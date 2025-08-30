import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ChatHistoryProvider } from './contexts/ChatHistoryContext'
import { UserProfile } from './components/auth/UserProfile'
import { PrivateRoute } from './components/auth/PrivateRoute'
import { AuthModal } from './components/auth/AuthModal'
import { ChatHistoryPanel } from './components/chat-history/ChatHistoryPanel'

function AppContent() {
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showChatHistory, setShowChatHistory] = useState(false)
  const { isAuthenticated } = useAuth()

  return (
    <div className={`min-h-screen ${isDarkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors flex flex-col">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              {isAuthenticated && (
                <button
                  onClick={() => setShowChatHistory(!showChatHistory)}
                  className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  aria-label="Toggle chat history"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              )}
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Oneline Chat
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                aria-label="Toggle dark mode"
              >
                {isDarkMode ? '☀️' : '🌙'}
              </button>
              {isAuthenticated ? (
                <UserProfile />
              ) : (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar - Desktop */}
          {isAuthenticated && showChatHistory && (
            <div className="hidden md:flex">
              <ChatHistoryPanel
                isOpen={true}
                onClose={() => setShowChatHistory(false)}
                isMobile={false}
              />
            </div>
          )}

          {/* Main Content */}
          <main className="flex-1 overflow-hidden">
            <div className="h-full p-4 sm:p-6 lg:p-8">
              <PrivateRoute>
                <ChatInterface />
              </PrivateRoute>
            </div>
          </main>
        </div>

        {/* Sidebar - Mobile Overlay */}
        {isAuthenticated && showChatHistory && (
          <div className="md:hidden">
            <ChatHistoryPanel
              isOpen={true}
              onClose={() => setShowChatHistory(false)}
              isMobile={true}
            />
          </div>
        )}

        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
        />
      </div>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <ChatHistoryProvider>
        <AppContent />
      </ChatHistoryProvider>
    </AuthProvider>
  )
}

export default App