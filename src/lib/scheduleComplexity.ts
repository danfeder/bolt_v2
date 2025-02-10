import type { Class, TeacherAvailability, ScheduleConstraints } from '../types';

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

  // Decision thresholds for using dev solver
  const useDev = 
    totalClasses > 20 ||                  // Many classes
    constraintComplexity > 80 ||          // Very complex constraints
    teacherConflicts > 30 ||              // Many teacher conflicts
    overallComplexity > 70;               // High overall complexity

  if (useDev) {
    return {
      solverVersion: 'dev',
      reason: determineSolverReason(metrics, 'dev'),
      metrics
    };
  }

  return {
    solverVersion: 'stable',
    reason: determineSolverReason(metrics, 'stable'),
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

function determineSolverReason(metrics: ComplexityMetrics, version: 'stable' | 'dev'): string {
  const reasons: string[] = [];

  if (version === 'dev') {
    if (metrics.totalClasses > 20) {
      reasons.push('large number of classes');
    }
    if (metrics.constraintComplexity > 80) {
      reasons.push('very complex scheduling constraints');
    }
    if (metrics.teacherConflicts > 30) {
      reasons.push('high number of teacher conflicts');
    }
    if (metrics.overallComplexity > 70) {
      reasons.push('high overall scheduling complexity');
    }
    return `Using development solver for ${reasons.join(' and ')}`;
  } else {
    return 'Using stable solver for standard scheduling complexity';
  }
}
