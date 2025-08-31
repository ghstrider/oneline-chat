import React, { useState, useMemo } from 'react';
import { Agent } from '../../hooks/useAgents';

interface AgentSidebarProps {
  agents: Agent[];
  selectedAgent: Agent | null;
  onAgentSelect: (agent: Agent) => void;
  loading?: boolean;
}

const AgentSidebar: React.FC<AgentSidebarProps> = ({
  agents,
  selectedAgent,
  onAgentSelect,
  loading = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgents = useMemo(() => {
    if (!searchQuery.trim()) return agents;
    
    const query = searchQuery.toLowerCase();
    return agents.filter(agent => 
      agent.name.toLowerCase().includes(query) ||
      agent.model.toLowerCase().includes(query) ||
      agent.type.toLowerCase().includes(query) ||
      agent.capabilities.some(cap => cap.toLowerCase().includes(query))
    );
  }, [agents, searchQuery]);

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

  const getAgentIcon = (agent: Agent) => {
    return agent.avatar_url || '🤖';
  };

  const getRoleLabel = (agent: Agent) => {
    switch (agent.type) {
      case 'system':
        return 'System';
      case 'specialized':
        return 'Specialist';
      case 'custom':
        return 'Custom';
      default:
        return agent.type;
    }
  };

  return (
    <div className="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
          AGENTS
        </h3>
        
        {/* Search Bar */}
        <div className="relative">
          <svg 
            className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 
                     rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Agent List */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="p-4 text-center">
            <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto" />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Loading agents...</p>
          </div>
        )}

        {!loading && filteredAgents.length === 0 && (
          <div className="p-4 text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No agents found matching your search' : 'No agents available'}
            </p>
          </div>
        )}

        {!loading && filteredAgents.map((agent) => (
          <div
            key={agent.id}
            onClick={() => onAgentSelect(agent)}
            className={`p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer
                       hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                       ${selectedAgent?.id === agent.id ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700' : ''}`}
          >
            <div className="flex items-start space-x-3">
              {/* Agent Icon & Status */}
              <div className="relative flex-shrink-0">
                <span className="text-xl">{getAgentIcon(agent)}</span>
                <span className="absolute -bottom-1 -right-1 text-xs">
                  {getStatusDot(agent.status)}
                </span>
              </div>

              {/* Agent Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {agent.name}
                  </h4>
                </div>
                
                <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">
                  {getRoleLabel(agent)}
                </p>
                
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  {agent.model}
                </p>

                {/* Capabilities Tags */}
                {agent.capabilities.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.slice(0, 3).map((capability, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 
                                 text-gray-700 dark:text-gray-300 rounded"
                      >
                        {capability}
                      </span>
                    ))}
                    {agent.capabilities.length > 3 && (
                      <span className="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                        +{agent.capabilities.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Response Time */}
            {agent.response_time_ms && (
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                ~{Math.round(agent.response_time_ms / 1000)}s response time
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Custom Agent Button */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button className="w-full flex items-center justify-center space-x-2 py-2 px-4 
                         border-2 border-dashed border-gray-300 dark:border-gray-600 
                         rounded-lg text-gray-600 dark:text-gray-400 
                         hover:border-blue-400 hover:text-blue-600 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span className="text-sm font-medium">Add Custom Agent</span>
        </button>
      </div>
    </div>
  );
};

export default AgentSidebar;