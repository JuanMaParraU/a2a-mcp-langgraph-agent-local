import { create } from 'zustand';
import { MetricsSnapshot, TimeSeriesPoint } from '@/lib/types';
import { computePercentile, computeTokensPerSecond } from '@/lib/utils';

const MAX_TIME_SERIES_POINTS = 60;
const POLL_INTERVAL_SECONDS = 5;

interface MetricsStore {
  current: MetricsSnapshot | null;
  timeSeries: TimeSeriesPoint[];
  isAvailable: boolean;
  modelName: string;
  addSnapshot: (snapshot: MetricsSnapshot) => void;
  setUnavailable: () => void;
  setAvailable: () => void;
}

export const useMetricsStore = create<MetricsStore>((set, get) => ({
  current: null,
  timeSeries: [],
  isAvailable: true,
  modelName: 'No Model Detected',

  addSnapshot: (snapshot: MetricsSnapshot) => {
    const state = get();
    const previousTokensTotal = state.current?.tokens_total ?? snapshot.tokens_total;

    const sortedLatencies = [...snapshot.submission_latencies].sort((a, b) => a - b);

    const point: TimeSeriesPoint = {
      timestamp: Date.now(),
      tokensPerSecond: computeTokensPerSecond(
        snapshot.tokens_total,
        previousTokensTotal,
        POLL_INTERVAL_SECONDS
      ),
      avgLatency: snapshot.avg_latency,
      p50Latency: computePercentile(sortedLatencies, 50),
      p95Latency: computePercentile(sortedLatencies, 95),
      p99Latency: computePercentile(sortedLatencies, 99),
    };

    const updatedTimeSeries = [...state.timeSeries, point];
    if (updatedTimeSeries.length > MAX_TIME_SERIES_POINTS) {
      updatedTimeSeries.shift();
    }

    set({
      current: snapshot,
      timeSeries: updatedTimeSeries,
      modelName: snapshot.model ?? 'No Model Detected',
    });
  },

  setUnavailable: () => {
    set({ isAvailable: false });
  },

  setAvailable: () => {
    set({ isAvailable: true });
  },
}));
