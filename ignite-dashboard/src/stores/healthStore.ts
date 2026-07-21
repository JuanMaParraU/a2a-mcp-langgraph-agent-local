import { create } from 'zustand';
import { AgentStatus, GlobalStatus, AgentHealthState, AgentCard } from '@/lib/types';
import { AGENT_NODES } from '@/lib/config';

interface HealthStore {
  agents: Record<string, AgentHealthState>;
  globalStatus: GlobalStatus;
  activeCount: number;
  totalCount: number;
  setAgentStatus: (agentId: string, status: AgentStatus, card?: AgentCard) => void;
  getGlobalStatus: () => GlobalStatus;
}

function deriveGlobalStatus(agents: Record<string, AgentHealthState>): GlobalStatus {
  const states = Object.values(agents);

  if (states.length === 0) {
    return 'checking';
  }

  const hasChecking = states.some((a) => a.status === 'checking');
  if (hasChecking) {
    return 'checking';
  }

  const allOnline = states.every((a) => a.status === 'online');
  if (allOnline) {
    return 'online';
  }

  const allOffline = states.every((a) => a.status === 'offline');
  if (allOffline) {
    return 'offline';
  }

  return 'degraded';
}

function deriveActiveCount(agents: Record<string, AgentHealthState>): number {
  return Object.values(agents).filter((a) => a.status === 'online').length;
}

// Initialize all agents from AGENT_NODES in "checking" state
const initialAgents: Record<string, AgentHealthState> = {};
for (const node of AGENT_NODES) {
  initialAgents[node.id] = {
    agentId: node.id,
    status: 'checking',
    lastChecked: 0,
    agentCard: null,
  };
}

export const useHealthStore = create<HealthStore>((set, get) => ({
  agents: initialAgents,
  globalStatus: deriveGlobalStatus(initialAgents),
  activeCount: deriveActiveCount(initialAgents),
  totalCount: AGENT_NODES.length,

  setAgentStatus: (agentId: string, status: AgentStatus, card?: AgentCard) => {
    set((state) => {
      const updatedAgents = {
        ...state.agents,
        [agentId]: {
          agentId,
          status,
          lastChecked: Date.now(),
          agentCard: card ?? state.agents[agentId]?.agentCard ?? null,
        },
      };

      return {
        agents: updatedAgents,
        globalStatus: deriveGlobalStatus(updatedAgents),
        activeCount: deriveActiveCount(updatedAgents),
        totalCount: Object.keys(updatedAgents).length,
      };
    });
  },

  getGlobalStatus: () => {
    return get().globalStatus;
  },
}));
