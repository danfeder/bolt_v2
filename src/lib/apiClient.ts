import type { 
  Class, 
  ScheduleAssignment, 
  ScheduleConstraints, 
  TeacherAvailability,
  ScheduleMetadata 
} from '../types';
import type { ComparisonResult } from '../store/types';

interface ScheduleRequest {
  classes: Class[];
  teacherAvailability: TeacherAvailability[];
  startDate: string;
  endDate: string;
  constraints: {
    maxClassesPerDay: number;
    maxClassesPerWeek: number;
    minPeriodsPerWeek: number;
    maxConsecutiveClasses: 1 | 2;
    consecutiveClassesRule: 'hard' | 'soft';
    startDate: string;  // Added to match backend expectations
    endDate: string;    // Added to match backend expectations
  };
}

interface ScheduleResponse {
  assignments: ScheduleAssignment[];
  metadata: ScheduleMetadata;
}

interface ValidationError {
  detail: string;
  errors: Array<{
    location: string;
    message: string;
    type: string;
  }>;
}

const SCHEDULER_URL = import.meta.env.PROD 
  ? '/api'  // Production URL (will update with Render URL)
  : 'http://localhost:8000';  // FastAPI development URL

type SchedulerVersion = 'stable' | 'dev';

export async function generateScheduleWithOrTools(
  classes: Class[],
  teacherAvailability: TeacherAvailability[],
  constraints: ScheduleConstraints,
  version: SchedulerVersion = 'stable'
): Promise<{ assignments: ScheduleAssignment[]; metadata: ScheduleResponse['metadata'] }> {
  const request: ScheduleRequest = {
    classes,
    teacherAvailability,
    startDate: constraints.startDate,
    endDate: constraints.endDate,
    constraints: {
      maxClassesPerDay: constraints.maxClassesPerDay,
      maxClassesPerWeek: constraints.maxClassesPerWeek,
      minPeriodsPerWeek: constraints.minPeriodsPerWeek,
      maxConsecutiveClasses: constraints.maxConsecutiveClasses,
      consecutiveClassesRule: constraints.consecutiveClassesRule,
      startDate: constraints.startDate,
      endDate: constraints.endDate
    },
  };

  try {
    // Use explicit endpoint paths instead of query parameters
    const url = `${SCHEDULER_URL}/schedule/${version}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 422 && 'errors' in data) {
        const validationError = data as ValidationError;
        const errorMessage = validationError.errors
          .map(err => `${err.location}: ${err.message}`)
          .join('\n');
        throw new Error(`Validation error:\n${errorMessage}`);
      }
      throw new Error(data.detail || data.message || 'Failed to generate schedule');
    }

    return {
      assignments: data.assignments,
      metadata: data.metadata,
    };
  } catch (error) {
    console.error('Schedule generation error:', error);
    throw error;
  }
}

export async function compareScheduleSolvers(
  classes: Class[],
  teacherAvailability: TeacherAvailability[],
  constraints: ScheduleConstraints
): Promise<ComparisonResult> {
  const request: ScheduleRequest = {
    classes,
    teacherAvailability,
    startDate: constraints.startDate,
    endDate: constraints.endDate,
    constraints: {
      maxClassesPerDay: constraints.maxClassesPerDay,
      maxClassesPerWeek: constraints.maxClassesPerWeek,
      minPeriodsPerWeek: constraints.minPeriodsPerWeek,
      maxConsecutiveClasses: constraints.maxConsecutiveClasses,
      consecutiveClassesRule: constraints.consecutiveClassesRule,
      startDate: constraints.startDate,
      endDate: constraints.endDate
    },
  };

  try {
    const url = `${SCHEDULER_URL}/schedule/compare`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 422 && 'errors' in data) {
        const validationError = data as ValidationError;
        const errorMessage = validationError.errors
          .map(err => `${err.location}: ${err.message}`)
          .join('\n');
        throw new Error(`Validation error:\n${errorMessage}`);
      }
      throw new Error(data.detail || data.message || 'Failed to compare schedules');
    }
    
    // Transform API response to match ComparisonResult type
    return {
      stable: data.stable,
      dev: data.dev,
      differences: data.comparison.assignment_differences,
      metrics: data.comparison.metric_differences
    };
  } catch (error) {
    console.error('Schedule comparison error:', error);
    throw error;
  }
}
