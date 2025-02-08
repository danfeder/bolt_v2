import { Class, TeacherAvailability, ScheduleAssignment } from '../../src/types';

export interface ScheduleRequest {
  classes: Class[];
  teacherAvailability: TeacherAvailability[];
  startDate: string;  // ISO date string
  endDate: string;    // ISO date string
  constraints: {
    maxClassesPerDay: number;
    maxClassesPerWeek: number;
    minPeriodsPerWeek: number;
    maxConsecutiveClasses: 1 | 2;
    consecutiveClassesRule: 'hard' | 'soft';
  };
}

export interface ScheduleResponse {
  assignments: ScheduleAssignment[];
  metadata: {
    solver: 'or-tools' | 'backtracking';
    duration: number;  // in milliseconds
    score: number;     // optimization score
  };
}

export interface ScheduleResult {
  assignments: ScheduleAssignment[];
  duration: number;
  score: number;
}
