'use client';

import React, { useRef } from 'react';

interface GaugeProps {
  value: number;
  label: string;
  color?: string;
}

/**
 * Gauge - Circular gauge component with auto-scaling max.
 * The gauge maximum is 120% of the highest observed value for the metric.
 * Uses SVG circle with stroke-dasharray for progress visualization.
 */
export function Gauge({ value, label, color = '#00d4ff' }: GaugeProps) {
  const highestRef = useRef<number>(0);

  // Track the highest observed value
  if (value > highestRef.current) {
    highestRef.current = value;
  }

  // Auto-scaling: max = 120% of highest observed value (minimum 1 to avoid division by zero)
  const gaugeMax = Math.max(highestRef.current * 1.2, 1);
  const percentage = Math.min(value / gaugeMax, 1);

  // SVG circle parameters
  const size = 80;
  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - percentage);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
        aria-label={`${label}: ${value}`}
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-300"
        />
      </svg>
      {/* Value displayed centered over the SVG */}
      <span
        className="font-mono text-sm font-bold -mt-[54px] mb-[30px]"
        style={{ color }}
      >
        {value}
      </span>
      {/* Label below the circle */}
      <span className="text-xs text-gray-400">{label}</span>
    </div>
  );
}
