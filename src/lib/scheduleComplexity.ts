import type { Class, ScheduleConstraints } from '../types';

export interface ComplexityMetrics {
  totalClasses: number;
  totalDays: number;
  constraintComplexity: number;
  teacherConflicts: number;
  overallComplexity: number;
}

export interface SolverDecision {
  solverVersion: 'stable' | 'dev';
  reason: string;
  metrics: ComplexityMetrics;
}

/**
 * Analyzes schedule complexity to determine which solver version to use
 */
export function analyzeScheduleComplexity(
  classes: Class[],
  teacherAvailability: any[],
  constraints: ScheduleConstraints
): SolverDecision {
  // Calculate basic metrics
  const totalClasses = classes.length;
  const startDate = new Date(constraints.startDate);
  const endDate = new Date(constraints.endDate);
  const totalDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

  // Calculate constraint complexity
  const constraintComplexity = calculateConstraintComplexity(classes, constraints);
  
  // Calculate teacher conflict complexity
  const teacherConflicts = calculateTeacherConflicts(teacherAvailability);

  // Calculate overall complexity score (0-100)
  const overallComplexity = calculateOverallComplexity({
    totalClasses,
    totalDays,
    constraintComplexity,
    teacherConflicts,
    overallComplexity: 0 // placeholder, will be calculated
  });

  const metrics: ComplexityMetrics = {
    totalClasses,
    totalDays,
    constraintComplexity,
    teacherConflicts,
    overallComplexity
  };
  
  // Determine solver version based on complexity
  const solverVersion = overallComplexity > 70 ? 'dev' : 'stable';
  
  // Generate reason for decision
  const reason = determineSolverReason(metrics, solverVersion);
  
  return {
    solverVersion,
    reason,
    metrics
  };
}

/**
 * Calculate complexity based on constraints
 */
function calculateConstraintComplexity(
  classes: Class[],
  constraints: ScheduleConstraints
): number {
  let complexity = 0;

  // Base complexity from global constraints
  complexity += constraints.maxConsecutiveClasses === 1 ? 10 : 20;
  complexity += constraints.consecutiveClassesRule === 'hard' ? 15 : 5;
  
  // Class-specific constraints
  for (const classObj of classes) {
    // Required periods add significant complexity
    complexity += classObj.required_periods.length * 5;
    
    // Conflicts add moderate complexity
    complexity += classObj.conflicts.length * 3;
    
    // Since we don't have preferredPeriods and avoidPeriods in the Class interface,
    // we'll just add a base complexity for each class
    complexity += 2; // Base complexity for each class
  }

  // Normalize to 0-100 scale
  return Math.min(100, complexity);
}

/**
 * Calculate complexity from teacher availability conflicts
 */
function calculateTeacherConflicts(teacherAvailability: any[]): number {
  // Simple heuristic: more unavailable periods = more complexity
  return Math.min(100, teacherAvailability.length * 5);
}

/**
 * Calculate overall complexity score
 */
function calculateOverallComplexity(metrics: ComplexityMetrics): number {
  // Weighted sum of different complexity factors
  const weightedSum = 
    metrics.totalClasses * 0.3 + 
    metrics.constraintComplexity * 0.4 + 
    metrics.teacherConflicts * 0.3;
  
  // Normalize to 0-100 scale
  return Math.min(100, weightedSum);
}

/**
 * Generate a human-readable reason for the solver version decision
 */
function determineSolverReason(metrics: ComplexityMetrics, version: 'stable' | 'dev'): string {
  if (version === 'dev') {
    if (metrics.constraintComplexity > 70) {
      return 'Complex scheduling constraints require advanced solver capabilities';
    } else if (metrics.teacherConflicts > 70) {
      return 'High number of teacher availability conflicts';
    } else {
      return 'Overall schedule complexity exceeds threshold for stable solver';
    }
  } else {
    return 'Schedule complexity within normal range';
  }
}
