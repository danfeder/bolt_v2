import React from 'react';
import { SimplifiedSchedulerPanel } from './simplifiedScheduler/SimplifiedSchedulerPanel';

/**
 * SolverConfig component - provides an intuitive interface for configuring
 * the scheduling system. Designed for non-technical users with a focus on
 * simplicity and usability.
 * 
 * Features:
 * - Drag-and-drop priority ordering
 * - Simple instructor load settings
 * - Advanced options (hidden by default)
 */
export const SolverConfig: React.FC = () => {
  return <SimplifiedSchedulerPanel />;
};
