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
  metadata: {
    solver: 'or-tools' | 'backtracking';
    duration: number;
    score: number;
  };
}

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api'  // Production URL
  : 'http://localhost:3000/api';  // Development URL

export async function generateScheduleWithOrTools(
  classes: Class[],
  teacherAvailability: TeacherAvailability[],
  constraints: ScheduleConstraints
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
    const response = await fetch(`${API_BASE_URL}/schedule`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to generate schedule');
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
