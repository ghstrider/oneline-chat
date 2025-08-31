import React from 'react';
import { Agent } from '../../hooks/useAgents';

interface AgentTriggerButtonProps {
  activeAgent: Agent | null;
  onClick: () => void;
  loading?: boolean;
}

const AgentTriggerButton: React.FC<AgentTriggerButtonProps> = ({
  activeAgent,
  onClick,
  loading = false
}) => {
  const getAgentIcon = (agent: Agent | null) => {
    if (!agent) return '🤖';
    return agent.avatar_url || '🤖';
  };

  const getStatusDot = (status: string) => {
    switch (status) {
      case 'online':
        return '🟢';
      case 'busy':
        return '🟡';
      case 'offline':
        return '🔴';
      case 'error':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 
                 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors
                 border border-gray-300 dark:border-gray-600 min-w-0"
      title={activeAgent ? `Current agent: ${activeAgent.name}` : 'Select an agent'}
    >
      <div className="flex items-center space-x-1 min-w-0">
        <span className="text-lg flex-shrink-0">
          {getAgentIcon(activeAgent)}
        </span>
        
        {activeAgent && (
          <>
            <span className="text-xs">
              {getStatusDot(activeAgent.status)}
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
              {activeAgent.name}
            </span>
          </>
        )}
        
        {!activeAgent && (
          <span className="font-medium text-gray-600 dark:text-gray-400">
            Select Agent
          </span>
        )}
      </div>
      
      {loading && (
        <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin flex-shrink-0" />
      )}
      
      <svg 
        className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

export default AgentTriggerButton;