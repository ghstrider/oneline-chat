import React from 'react';
import { Agent } from '../../hooks/useAgents';

interface AgentDetailsProps {
  agent: Agent;
  onSelectPrimary: (agent: Agent) => void;
  onAddToConversation: (agent: Agent) => void;
  isActive?: boolean;
  loading?: boolean;
}

const AgentDetails: React.FC<AgentDetailsProps> = ({
  agent,
  onSelectPrimary,
  onAddToConversation,
  isActive = false,
  loading = false
}) => {
  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (status) {
      case 'online':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
      case 'busy':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
      case 'offline':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
      case 'error':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    }
  };

  const getProviderColor = (provider: string) => {
    const colors = {
      openai: 'text-green-600 dark:text-green-400',
      anthropic: 'text-orange-600 dark:text-orange-400',
      ollama: 'text-blue-600 dark:text-blue-400',
      custom: 'text-purple-600 dark:text-purple-400',
      gemini: 'text-red-600 dark:text-red-400'
    };
    return colors[provider as keyof typeof colors] || 'text-gray-600 dark:text-gray-400';
  };

  const formatLastCheck = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="flex-1 bg-white dark:bg-gray-800 p-6 overflow-y-auto">
      {/* Header Section */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{agent.avatar_url || '🤖'}</span>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {agent.name}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {agent.model} • {agent.provider}
              </p>
            </div>
          </div>
          <span className={getStatusBadge(agent.status)}>
            ● {agent.status}
          </span>
        </div>

        {agent.description && (
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            {agent.description}
          </p>
        )}
      </div>

      {/* Capabilities Section */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Capabilities
        </h3>
        {agent.capabilities.length > 0 ? (
          <div className="grid grid-cols-2 gap-2">
            {agent.capabilities.map((capability, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                  {capability.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">
            No specific capabilities listed
          </p>
        )}
      </div>

      {/* Specifications Grid */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Specifications
        </h3>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Type</span>
              <p className="text-sm text-gray-900 dark:text-gray-100 capitalize">{agent.type}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Provider</span>
              <p className={`text-sm font-medium ${getProviderColor(agent.provider)} capitalize`}>
                {agent.provider}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Response Time</span>
              <p className="text-sm text-gray-900 dark:text-gray-100">
                {agent.response_time_ms ? `~${Math.round(agent.response_time_ms / 1000)}s` : 'Unknown'}
              </p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Last Check</span>
              <p className="text-sm text-gray-900 dark:text-gray-100">
                {formatLastCheck(agent.last_health_check)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Information */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Current Status
        </h3>
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">
              {agent.status === 'online' ? '✅' : agent.status === 'busy' ? '⏳' : '❌'}
            </span>
            <span className="font-medium text-blue-900 dark:text-blue-100">
              {isActive ? 'Active in this chat' : 'Available for use'}
            </span>
          </div>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {agent.status === 'online' 
              ? 'Ready to assist with your requests' 
              : agent.status === 'busy'
              ? 'Currently processing other requests'
              : 'Currently unavailable'
            }
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3">
        <button
          onClick={() => onSelectPrimary(agent)}
          disabled={loading || agent.status !== 'online'}
          className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 
                   disabled:cursor-not-allowed text-white font-medium rounded-lg 
                   transition-colors flex items-center justify-center space-x-2"
        >
          {loading && (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          <span>{isActive ? 'Currently Selected' : 'Select as Primary'}</span>
        </button>

        <button
          onClick={() => onAddToConversation(agent)}
          disabled={loading || agent.status !== 'online'}
          className="w-full py-3 px-4 bg-white hover:bg-gray-50 disabled:bg-gray-100 
                   disabled:cursor-not-allowed dark:bg-gray-700 dark:hover:bg-gray-600
                   border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300
                   font-medium rounded-lg transition-colors"
        >
          Add to Conversation
        </button>

        <div className="grid grid-cols-2 gap-3">
          <button className="py-2 px-4 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 
                           dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 
                           text-sm font-medium rounded-lg transition-colors">
            Configure
          </button>
          <button className="py-2 px-4 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 
                           dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 
                           text-sm font-medium rounded-lg transition-colors">
            View History
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentDetails;