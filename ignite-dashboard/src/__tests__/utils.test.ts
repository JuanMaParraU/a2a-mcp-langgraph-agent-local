import { describe, it, expect } from 'vitest';
import { formatTimestamp, computePercentile, computeTokensPerSecond } from '@/lib/utils';

describe('formatTimestamp', () => {
  it('formats an ISO string as HH:mm:ss.SSS', () => {
    // Use a fixed UTC time and compare against local representation
    const iso = '2024-01-15T10:30:05.123Z';
    const result = formatTimestamp(iso);
    // Result depends on local timezone, but format should match pattern
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}\.\d{3}$/);
  });

  it('pads single-digit values with zeros', () => {
    // Create a date where we know the local time components
    const date = new Date(2024, 0, 1, 1, 2, 3, 4); // Jan 1, 2024, 01:02:03.004 local
    const result = formatTimestamp(date.toISOString());
    expect(result).toBe('01:02:03.004');
  });

  it('handles midnight correctly', () => {
    const date = new Date(2024, 0, 1, 0, 0, 0, 0);
    const result = formatTimestamp(date.toISOString());
    expect(result).toBe('00:00:00.000');
  });
});

describe('computePercentile', () => {
  it('returns 0 for empty array', () => {
    expect(computePercentile([], 50)).toBe(0);
  });

  it('returns the single value for a single-element array', () => {
    expect(computePercentile([42], 50)).toBe(42);
    expect(computePercentile([42], 95)).toBe(42);
  });

  it('computes p50 for a sorted array', () => {
    const sorted = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    const p50 = computePercentile(sorted, 50);
    expect(p50).toBe(5);
  });

  it('computes p95 for a sorted array', () => {
    const sorted = Array.from({ length: 100 }, (_, i) => i + 1);
    const p95 = computePercentile(sorted, 95);
    expect(p95).toBe(95);
  });

  it('computes p99 for a sorted array', () => {
    const sorted = Array.from({ length: 100 }, (_, i) => i + 1);
    const p99 = computePercentile(sorted, 99);
    expect(p99).toBe(99);
  });

  it('returns first element for percentile <= 0', () => {
    expect(computePercentile([1, 2, 3], 0)).toBe(1);
    expect(computePercentile([1, 2, 3], -10)).toBe(1);
  });

  it('returns last element for percentile >= 100', () => {
    expect(computePercentile([1, 2, 3], 100)).toBe(3);
    expect(computePercentile([1, 2, 3], 150)).toBe(3);
  });
});

describe('computeTokensPerSecond', () => {
  it('computes tokens per second correctly', () => {
    expect(computeTokensPerSecond(1000, 500, 5)).toBe(100);
  });

  it('returns 0 when interval is 0', () => {
    expect(computeTokensPerSecond(1000, 500, 0)).toBe(0);
  });

  it('returns 0 when interval is negative', () => {
    expect(computeTokensPerSecond(1000, 500, -1)).toBe(0);
  });

  it('returns 0 when token difference is negative', () => {
    expect(computeTokensPerSecond(500, 1000, 5)).toBe(0);
  });

  it('returns 0 when tokens are equal', () => {
    expect(computeTokensPerSecond(500, 500, 5)).toBe(0);
  });
});
