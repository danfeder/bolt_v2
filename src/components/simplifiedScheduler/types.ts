/**
 * Type definitions for the simplified scheduler components
 */

export interface Priority {
  id: string;
  name: string;
  description: string;
}

export interface InstructorLoadSettings {
  minPerDay: number;
  maxPerDay: number;
  minPerWeek: number;
  maxPerWeek: number;
  allowMinFlexibility: boolean;
  allowMaxFlexibility: boolean;
}

export interface AdvancedSettings {
  autoTuneWeights: boolean;
  requireBreakBetweenClasses: boolean;
}
