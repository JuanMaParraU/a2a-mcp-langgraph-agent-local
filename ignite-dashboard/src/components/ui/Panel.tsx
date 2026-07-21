'use client';

import React from 'react';

interface PanelProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Panel - Dark card wrapper component for dashboard panels.
 * Provides consistent styling: bg-card (#1a1a2e), rounded-lg (8px),
 * border at 20% opacity white, and padding.
 */
export function Panel({ children, className = '' }: PanelProps) {
  return (
    <div
      className={`bg-card rounded-lg border border-white/20 p-4 ${className}`.trim()}
    >
      {children}
    </div>
  );
}
