/**
 * Type definitions for constraint-related functionality
 */

// API response for constraint validation
export interface ConstraintValidationResponse {
  valid: boolean;
  errors: string[];
  incompatibleConstraints?: string[][];
  missingDependencies?: Record<string, string[]>;
}
