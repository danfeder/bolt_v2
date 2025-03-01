// Web Worker for handling scheduling computation
import Scheduler from './scheduler';
import type { Class, TeacherAvailability, ScheduleAssignment } from '../types';

interface ScheduleRequest {
  classes: Class[];
  teacherAvailability: TeacherAvailability[];
  startDate: string;
  endDate: string;
  maxClassesPerDay: number;
  maxClassesPerWeek: number;
  minPeriodsPerWeek: number;
  maxConsecutiveClasses: 1 | 2;
  consecutiveClassesRule: 'hard' | 'soft';
  version?: 'stable' | 'dev';
}

self.onmessage = async (e: MessageEvent<ScheduleRequest>) => {
  try {
    const scheduler = new Scheduler({
      ...e.data,
      startDate: new Date(e.data.startDate),
      endDate: new Date(e.data.endDate)
    });

    // Progress updates are now handled by the backend
    const assignments = await scheduler.solve(e.data.version);
    self.postMessage({ type: 'success', assignments });
  } catch (error) {
    self.postMessage({ 
      type: 'error', 
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};
