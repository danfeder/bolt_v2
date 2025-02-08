import type { Class, TeacherAvailability, ScheduleConstraints } from '../types';

export interface ComplexityMetrics {
  totalClasses: number;
  totalDays: number;
  constraintComplexity: number;
  teacherConflicts: number;
  overallComplexity: number;
}

export interface SolverDecision {
  solver: 'or-tools' | 'backtracking';
  reason: string;
  metrics: ComplexityMetrics;
}

/**
 * Analyzes schedule complexity to determine the appropriate solver
 */
export function analyzeScheduleComplexity(
  classes: Class[],
  teacherAvailability: TeacherAvailability[],
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

  // Decision thresholds
  const useOrTools = 
    totalClasses > 10 ||                  // Many classes
    constraintComplexity > 70 ||          // Complex constraints
    teacherConflicts > 20 ||              // Many teacher conflicts
    overallComplexity > 60;               // High overall complexity

  if (useOrTools) {
    return {
      solver: 'or-tools',
      reason: determineOrToolsReason(metrics),
      metrics
    };
  }

  return {
    solver: 'backtracking',
    reason: 'Schedule complexity is suitable for backtracking algorithm',
    metrics
  };
}

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
    complexity += classObj.weeklySchedule.requiredPeriods.length * 5;
    
    // Conflicts add moderate complexity
    complexity += classObj.weeklySchedule.conflicts.length * 3;
    
    // Preferences add slight complexity
    complexity += classObj.weeklySchedule.preferredPeriods.length;
    complexity += classObj.weeklySchedule.avoidPeriods.length;
  }

  // Normalize to 0-100 scale
  return Math.min(100, complexity);
}

function calculateTeacherConflicts(teacherAvailability: TeacherAvailability[]): number {
  return teacherAvailability.reduce(
    (total, ta) => total + ta.unavailableSlots.length,
    0
  );
}

function calculateOverallComplexity(metrics: ComplexityMetrics): number {
  const weights = {
    classes: 0.3,
    days: 0.1,
    constraints: 0.4,
    conflicts: 0.2
  };

  // Normalize each component to 0-100 scale
  const normalizedClasses = Math.min(100, (metrics.totalClasses / 20) * 100);
  const normalizedDays = Math.min(100, (metrics.totalDays / 30) * 100);

  return Math.min(100,
    normalizedClasses * weights.classes +
    normalizedDays * weights.days +
    metrics.constraintComplexity * weights.constraints +
    Math.min(100, (metrics.teacherConflicts / 30) * 100) * weights.conflicts
  );
}

function determineOrToolsReason(metrics: ComplexityMetrics): string {
  const reasons: string[] = [];

  if (metrics.totalClasses > 10) {
    reasons.push('large number of classes');
  }
  if (metrics.constraintComplexity > 70) {
    reasons.push('complex scheduling constraints');
  }
  if (metrics.teacherConflicts > 20) {
    reasons.push('significant teacher availability conflicts');
  }
  if (metrics.overallComplexity > 60) {
    reasons.push('high overall scheduling complexity');
  }

  return `Using OR-Tools due to ${reasons.join(' and ')}`;
}
