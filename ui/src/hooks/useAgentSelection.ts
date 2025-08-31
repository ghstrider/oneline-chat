import { useState, useEffect, useCallback, useRef } from 'react';
import { Agent } from './useAgents';

export const useAgentSelection = (chatId: string | null) => {
  const [activeAgent, setActiveAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectAgent = async (agentId: string, chatId: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/${agentId}/select?chat_id=${chatId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to select agent: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Fetch the full agent details
      const agentResponse = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/${agentId}`
      );
      
      if (agentResponse.ok) {
        const agent = await agentResponse.json();
        setActiveAgent(agent);
      }

      setError(null);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to select agent';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getActiveAgent = useCallback(async (chatId: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/chat/${chatId}/active`
      );

      if (!response.ok) {
        // If no active agent, try to get default
        const defaultResponse = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/default`
        );
        
        if (defaultResponse.ok) {
          const defaultAgent = await defaultResponse.json();
          setActiveAgent(defaultAgent);
          return defaultAgent;
        }
        
        setActiveAgent(null);
        return null;
      }

      const result = await response.json();
      
      // Fetch full agent details
      const agentResponse = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/${result.agent_id}`
      );
      
      if (agentResponse.ok) {
        const agent = await agentResponse.json();
        setActiveAgent(agent);
        return agent;
      }
      
      setActiveAgent(null);
      setError(null);
      return null;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get active agent');
      setActiveAgent(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const previousChatId = useRef<string | null>(null);

  // Load active agent when chatId changes
  useEffect(() => {
    // Only fetch if chatId actually changed
    if (chatId !== previousChatId.current) {
      previousChatId.current = chatId;
      
      if (chatId) {
        getActiveAgent(chatId);
      } else {
        // Load default agent if no chat
        fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/default`)
          .then(response => response.ok ? response.json() : null)
          .then(agent => setActiveAgent(agent))
          .catch(() => setActiveAgent(null));
      }
    }
  }, [chatId, getActiveAgent]);

  return {
    activeAgent,
    loading,
    error,
    selectAgent,
    getActiveAgent,
    clearError: () => setError(null)
  };
};