import { useState, useEffect, useCallback } from 'react';

export interface Agent {
  id: string;
  name: string;
  type: 'system' | 'custom' | 'specialized';
  provider: string;
  model: string;
  description?: string;
  capabilities: string[];
  avatar_url?: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  last_health_check?: string;
  response_time_ms?: number;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
  online_count: number;
}

export const useAgents = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async (includeOffline = false) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents?include_offline=${includeOffline}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.statusText}`);
      }
      
      const data: AgentListResponse = await response.json();
      setAgents(data.agents);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
    } finally {
      setLoading(false);
    }
  }, []);

  const getAgent = async (agentId: string): Promise<Agent | null> => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/${agentId}`
      );
      
      if (!response.ok) {
        return null;
      }
      
      return await response.json();
    } catch {
      return null;
    }
  };

  const getAgentStatus = async (agentId: string) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/${agentId}/status`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to get agent status: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to get agent status');
    }
  };

  const getDefaultAgent = async (): Promise<Agent | null> => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/agents/default`
      );
      
      if (!response.ok) {
        return null;
      }
      
      return await response.json();
    } catch {
      return null;
    }
  };

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return {
    agents,
    loading,
    error,
    fetchAgents,
    getAgent,
    getAgentStatus,
    getDefaultAgent,
    refresh: fetchAgents
  };
};