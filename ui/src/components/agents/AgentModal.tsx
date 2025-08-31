import React, { useState, useEffect, useCallback } from 'react';
import { useAgents, Agent } from '../../hooks/useAgents';
import { useAgentSelection } from '../../hooks/useAgentSelection';
import AgentSidebar from './AgentSidebar';
import AgentDetails from './AgentDetails';

interface AgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatId: string | null;
  onAgentSelected?: (agent: Agent) => void;
}

const AgentModal: React.FC<AgentModalProps> = ({
  isOpen,
  onClose,
  chatId,
  onAgentSelected
}) => {
  const { agents, loading: agentsLoading, error: agentsError } = useAgents();
  const { activeAgent, selectAgent, loading: selectionLoading, error: selectionError } = useAgentSelection(chatId);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Agents are automatically loaded by useAgents hook on mount
  // No need to refresh when modal opens

  useEffect(() => {
    if (activeAgent && !selectedAgent) {
      setSelectedAgent(activeAgent);
    }
  }, [activeAgent, selectedAgent]);

  const handleAgentSelect = useCallback((agent: Agent) => {
    setSelectedAgent(agent);
  }, []);

  const handleSelectPrimary = useCallback(async (agent: Agent) => {
    if (!chatId) {
      console.warn('No chat ID available for agent selection');
      return;
    }

    try {
      setActionLoading(true);
      await selectAgent(agent.id, chatId);
      onAgentSelected?.(agent);
      onClose();
    } catch (error) {
      console.error('Failed to select agent:', error);
    } finally {
      setActionLoading(false);
    }
  }, [chatId, selectAgent, onAgentSelected, onClose]);

  const handleAddToConversation = useCallback(async (agent: Agent) => {
    // For solo mode, this is the same as selecting primary
    await handleSelectPrimary(agent);
  }, [handleSelectPrimary]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative flex items-center justify-center min-h-screen p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex">
          {/* Header */}
          <div className="absolute top-0 left-0 right-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 rounded-t-lg">
            <div className="flex items-center justify-between p-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Agents Available for You
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex w-full mt-16">
            {/* Sidebar */}
            <AgentSidebar
              agents={agents}
              selectedAgent={selectedAgent}
              onAgentSelect={handleAgentSelect}
              loading={agentsLoading}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
              {/* Error Display */}
              {(agentsError || selectionError) && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                  <div className="flex items-center space-x-2">
                    <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <p className="text-sm text-red-700 dark:text-red-300">
                      {agentsError || selectionError}
                    </p>
                  </div>
                </div>
              )}

              {/* Agent Details */}
              {selectedAgent ? (
                <AgentDetails
                  agent={selectedAgent}
                  onSelectPrimary={handleSelectPrimary}
                  onAddToConversation={handleAddToConversation}
                  isActive={activeAgent?.id === selectedAgent.id}
                  loading={actionLoading || selectionLoading}
                />
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                      Select an Agent
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm">
                      Choose an agent from the sidebar to view its capabilities and configuration options.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Loading Overlay */}
          {agentsLoading && agents.length === 0 && (
            <div className="absolute inset-0 bg-white dark:bg-gray-800 flex items-center justify-center rounded-lg">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Loading agents...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentModal;