import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('config module', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('uses default values when env vars are not set', async () => {
    delete process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;
    delete process.env.NEXT_PUBLIC_RESEARCH_AGENT_URL;
    delete process.env.NEXT_PUBLIC_MCP_SERVER_URL;

    const { config } = await import('@/lib/config');

    expect(config.ORCHESTRATOR_URL).toBe('http://localhost:9990');
    expect(config.RESEARCH_AGENT_URL).toBe('http://localhost:9991');
    expect(config.MCP_SERVER_URL).toBe('http://localhost:8000');
  });

  it('uses environment variable values when set', async () => {
    process.env.NEXT_PUBLIC_ORCHESTRATOR_URL = 'http://custom:1111';
    process.env.NEXT_PUBLIC_RESEARCH_AGENT_URL = 'http://custom:2222';
    process.env.NEXT_PUBLIC_MCP_SERVER_URL = 'http://custom:3333';

    const { config } = await import('@/lib/config');

    expect(config.ORCHESTRATOR_URL).toBe('http://custom:1111');
    expect(config.RESEARCH_AGENT_URL).toBe('http://custom:2222');
    expect(config.MCP_SERVER_URL).toBe('http://custom:3333');
  });

  it('logs a warning for missing environment variables', async () => {
    delete process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    await import('@/lib/config');

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('NEXT_PUBLIC_ORCHESTRATOR_URL')
    );
    warnSpy.mockRestore();
  });

  it('exports AGENT_NODES with correct structure', async () => {
    const { AGENT_NODES } = await import('@/lib/config');

    expect(AGENT_NODES).toHaveLength(3);
    expect(AGENT_NODES[0]).toMatchObject({
      id: 'orchestrator',
      name: 'Orchestrator Agent',
      type: 'orchestrator',
      port: 9990,
    });
    expect(AGENT_NODES[1]).toMatchObject({
      id: 'research-agent',
      name: 'Research Agent',
      type: 'worker',
      port: 9991,
    });
    expect(AGENT_NODES[2]).toMatchObject({
      id: 'mcp-server',
      name: 'MCP Server',
      type: 'mcp',
      port: 8000,
    });
  });

  it('exports TOPOLOGY_EDGES with correct connections', async () => {
    const { TOPOLOGY_EDGES } = await import('@/lib/config');

    expect(TOPOLOGY_EDGES).toHaveLength(2);
    expect(TOPOLOGY_EDGES[0]).toEqual({
      source: 'orchestrator',
      target: 'research-agent',
      label: 'A2A',
    });
    expect(TOPOLOGY_EDGES[1]).toEqual({
      source: 'research-agent',
      target: 'mcp-server',
      label: 'MCP',
    });
  });
});
