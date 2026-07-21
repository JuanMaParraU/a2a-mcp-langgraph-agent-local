import { describe, it, expect, beforeEach } from 'vitest';
import { useMetricsStore } from '@/stores/metricsStore';
import { MetricsSnapshot } from '@/lib/types';

function createSnapshot(overrides: Partial<MetricsSnapshot> = {}): MetricsSnapshot {
  return {
    timestamp: '2024-01-15T10:30:00.000Z',
    model: 'qwen3:4b',
    requests_total: 10,
    errors_total: 0,
    inter_agent_messages: 5,
    tool_calls: 3,
    retrievals: 2,
    tokens_total: 1000,
    tokens_prompt: 600,
    tokens_completion: 400,
    submission_latencies: [0.1, 0.3, 0.5, 0.8, 1.0],
    task_durations: [2.0, 3.0],
    tools_used: ['duckduckgo_search'],
    ai_messages_count: 8,
    reasoning_steps: 6,
    avg_latency: 0.54,
    avg_task_duration: 2.5,
    tokens_per_request: 100,
    tools_per_request: 0.3,
    ...overrides,
  };
}

describe('metricsStore', () => {
  beforeEach(() => {
    useMetricsStore.setState({
      current: null,
      timeSeries: [],
      isAvailable: true,
      modelName: 'No Model Detected',
    });
  });

  describe('initial state', () => {
    it('should have null current snapshot', () => {
      const state = useMetricsStore.getState();
      expect(state.current).toBeNull();
    });

    it('should have empty timeSeries', () => {
      const state = useMetricsStore.getState();
      expect(state.timeSeries).toEqual([]);
    });

    it('should be available by default', () => {
      const state = useMetricsStore.getState();
      expect(state.isAvailable).toBe(true);
    });

    it('should have "No Model Detected" as default modelName', () => {
      const state = useMetricsStore.getState();
      expect(state.modelName).toBe('No Model Detected');
    });
  });

  describe('addSnapshot', () => {
    it('should store the snapshot as current', () => {
      const snapshot = createSnapshot();
      useMetricsStore.getState().addSnapshot(snapshot);
      expect(useMetricsStore.getState().current).toEqual(snapshot);
    });

    it('should add a TimeSeriesPoint to timeSeries', () => {
      const snapshot = createSnapshot();
      useMetricsStore.getState().addSnapshot(snapshot);
      const state = useMetricsStore.getState();
      expect(state.timeSeries).toHaveLength(1);
      expect(state.timeSeries[0].avgLatency).toBe(0.54);
    });

    it('should compute tokensPerSecond as 0 for the first snapshot', () => {
      const snapshot = createSnapshot({ tokens_total: 1000 });
      useMetricsStore.getState().addSnapshot(snapshot);
      const state = useMetricsStore.getState();
      // First snapshot: previousTokens = current tokens, so diff = 0
      expect(state.timeSeries[0].tokensPerSecond).toBe(0);
    });

    it('should compute tokensPerSecond from consecutive snapshots', () => {
      const first = createSnapshot({ tokens_total: 1000 });
      const second = createSnapshot({ tokens_total: 1050 });
      useMetricsStore.getState().addSnapshot(first);
      useMetricsStore.getState().addSnapshot(second);
      const state = useMetricsStore.getState();
      // (1050 - 1000) / 5 = 10
      expect(state.timeSeries[1].tokensPerSecond).toBe(10);
    });

    it('should compute percentiles from submission_latencies', () => {
      const snapshot = createSnapshot({
        submission_latencies: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
      });
      useMetricsStore.getState().addSnapshot(snapshot);
      const state = useMetricsStore.getState();
      const point = state.timeSeries[0];
      expect(point.p50Latency).toBe(0.5);
      expect(point.p95Latency).toBe(1.0);
      expect(point.p99Latency).toBe(1.0);
    });

    it('should derive modelName from snapshot.model', () => {
      const snapshot = createSnapshot({ model: 'gpt-4' });
      useMetricsStore.getState().addSnapshot(snapshot);
      expect(useMetricsStore.getState().modelName).toBe('gpt-4');
    });

    it('should use "No Model Detected" when model is null', () => {
      const snapshot = createSnapshot({ model: null });
      useMetricsStore.getState().addSnapshot(snapshot);
      expect(useMetricsStore.getState().modelName).toBe('No Model Detected');
    });

    it('should set timestamp on TimeSeriesPoint', () => {
      const before = Date.now();
      useMetricsStore.getState().addSnapshot(createSnapshot());
      const after = Date.now();
      const point = useMetricsStore.getState().timeSeries[0];
      expect(point.timestamp).toBeGreaterThanOrEqual(before);
      expect(point.timestamp).toBeLessThanOrEqual(after);
    });
  });

  describe('circular buffer (max 60 points)', () => {
    it('should not exceed 60 items in timeSeries', () => {
      const store = useMetricsStore.getState();
      for (let i = 0; i < 65; i++) {
        store.addSnapshot(createSnapshot({ tokens_total: i * 100 }));
      }
      expect(useMetricsStore.getState().timeSeries).toHaveLength(60);
    });

    it('should discard the oldest point when exceeding 60', () => {
      const store = useMetricsStore.getState();
      // Add 61 snapshots
      for (let i = 0; i <= 60; i++) {
        store.addSnapshot(createSnapshot({ tokens_total: i * 100 }));
      }
      const state = useMetricsStore.getState();
      expect(state.timeSeries).toHaveLength(60);
      // The first point should have been discarded
      // Second snapshot had tokens_total=100, previous was 0, so tokensPerSecond = 100/5 = 20
      expect(state.timeSeries[0].tokensPerSecond).toBe(20);
    });
  });

  describe('setUnavailable / setAvailable', () => {
    it('should set isAvailable to false', () => {
      useMetricsStore.getState().setUnavailable();
      expect(useMetricsStore.getState().isAvailable).toBe(false);
    });

    it('should set isAvailable to true', () => {
      useMetricsStore.getState().setUnavailable();
      useMetricsStore.getState().setAvailable();
      expect(useMetricsStore.getState().isAvailable).toBe(true);
    });
  });
});
