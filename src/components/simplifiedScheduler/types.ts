/**
 * Type definitions for the simplified scheduler components
 */

// Priority interface enhanced with support for constraint categories
export interface Priority {
  id: string;
  name: string;
  description: string;
  // Enhanced fields for constraint integration
  constraintCategory?: string;
  constraintIds?: string[];
}

export interface InstructorLoadSettings {
  minPerDay: number;
  maxPerDay: number;
  minPerWeek: number;
  maxPerWeek: number;
  allowMinFlexibility: boolean;
  allowMaxFlexibility: boolean;
}

// Extended with support for constraint relaxation and validation
export interface AdvancedSettings {
  autoTuneWeights: boolean;
  requireBreakBetweenClasses: boolean;
  // New fields for enhanced constraint system
  relaxIncompatibleConstraints: boolean;
  strictValidation: boolean;
  enabledCategories: string[];
  // Start date for scheduling
  startDate?: Date;
}

// The result of validating constraints
export interface ConstraintValidationResult {
  isValid: boolean;
  messages: string[];
  incompatibleConstraints?: string[][];
  missingDependencies?: Record<string, string[]>;
}
