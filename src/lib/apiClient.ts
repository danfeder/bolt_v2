import type { Class, ScheduleAssignment, ScheduleConstraints, TeacherAvailability } from '../types';

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
  };
}

interface ScheduleResponse {
  assignments: ScheduleAssignment[];
  metadata: import('../types').ScheduleMetadata;  // Use the shared type definition
}

const SCHEDULER_URL = import.meta.env.PROD 
  ? '/api'  // Production URL (will update with Render URL)
  : 'http://localhost:8000';  // FastAPI development URL

type SchedulerVersion = 'stable' | 'dev';  // Match Python backend versions

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
    },
  };

  try {
    const url = new URL(`${SCHEDULER_URL}/schedule`);
    url.searchParams.set('version', version);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.message || 'Failed to generate schedule');
    }

    const data: ScheduleResponse = await response.json();
    return {
      assignments: data.assignments,
      metadata: data.metadata,
    };
  } catch (error) {
    console.error('Schedule generation error:', error);
    throw error;
  }
}
