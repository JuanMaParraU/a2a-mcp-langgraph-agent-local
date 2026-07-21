import { describe, it, expect, beforeEach } from 'vitest';
import { useHealthStore } from '@/stores/healthStore';

describe('healthStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useHealthStore.setState({
      agents: {
        orchestrator: { agentId: 'orchestrator', status: 'checking', lastChecked: 0, agentCard: null },
        'research-agent': { agentId: 'research-agent', status: 'checking', lastChecked: 0, agentCard: null },
        'mcp-server': { agentId: 'mcp-server', status: 'checking', lastChecked: 0, agentCard: null },
      },
      globalStatus: 'checking',
      activeCount: 0,
      totalCount: 3,
    });
  });

  it('initializes with 3 agents in checking state', () => {
    const state = useHealthStore.getState();
    expect(state.totalCount).toBe(3);
    expect(state.activeCount).toBe(0);
    expect(state.globalStatus).toBe('checking');
    expect(state.agents['orchestrator'].status).toBe('checking');
    expect(state.agents['research-agent'].status).toBe('checking');
    expect(state.agents['mcp-server'].status).toBe('checking');
  });

  it('sets agent status to online and updates derived state', () => {
    const { setAgentStatus } = useHealthStore.getState();

    setAgentStatus('orchestrator', 'online');
    setAgentStatus('research-agent', 'online');
    setAgentStatus('mcp-server', 'online');

    const state = useHealthStore.getState();
    expect(state.globalStatus).toBe('online');
    expect(state.activeCount).toBe(3);
    expect(state.totalCount).toBe(3);
  });

  it('derives degraded status when mixed online/offline', () => {
    const { setAgentStatus } = useHealthStore.getState();

    setAgentStatus('orchestrator', 'online');
    setAgentStatus('research-agent', 'offline');
    setAgentStatus('mcp-server', 'online');

    const state = useHealthStore.getState();
    expect(state.globalStatus).toBe('degraded');
    expect(state.activeCount).toBe(2);
  });

  it('derives offline status when all agents are offline', () => {
    const { setAgentStatus } = useHealthStore.getState();

    setAgentStatus('orchestrator', 'offline');
    setAgentStatus('research-agent', 'offline');
    setAgentStatus('mcp-server', 'offline');

    const state = useHealthStore.getState();
    expect(state.globalStatus).toBe('offline');
    expect(state.activeCount).toBe(0);
  });

  it('derives checking status when any agent is still checking', () => {
    const { setAgentStatus } = useHealthStore.getState();

    setAgentStatus('orchestrator', 'online');
    setAgentStatus('research-agent', 'online');
    // mcp-server remains 'checking'

    const state = useHealthStore.getState();
    expect(state.globalStatus).toBe('checking');
  });

  it('stores agent card when provided', () => {
    const { setAgentStatus } = useHealthStore.getState();
    const card = { name: 'Orchestrator Agent', description: 'Main orchestrator' };

    setAgentStatus('orchestrator', 'online', card);

    const state = useHealthStore.getState();
    expect(state.agents['orchestrator'].agentCard).toEqual(card);
  });

  it('preserves existing agent card when not provided in update', () => {
    const { setAgentStatus } = useHealthStore.getState();
    const card = { name: 'Orchestrator Agent', description: 'Main orchestrator' };

    setAgentStatus('orchestrator', 'online', card);
    setAgentStatus('orchestrator', 'offline'); // no card provided

    const state = useHealthStore.getState();
    expect(state.agents['orchestrator'].agentCard).toEqual(card);
    expect(state.agents['orchestrator'].status).toBe('offline');
  });

  it('updates lastChecked timestamp on status change', () => {
    const { setAgentStatus } = useHealthStore.getState();
    const before = Date.now();

    setAgentStatus('orchestrator', 'online');

    const state = useHealthStore.getState();
    expect(state.agents['orchestrator'].lastChecked).toBeGreaterThanOrEqual(before);
  });

  it('getGlobalStatus returns current global status', () => {
    const { setAgentStatus, getGlobalStatus } = useHealthStore.getState();

    setAgentStatus('orchestrator', 'online');
    setAgentStatus('research-agent', 'online');
    setAgentStatus('mcp-server', 'online');

    expect(useHealthStore.getState().getGlobalStatus()).toBe('online');
  });
});
