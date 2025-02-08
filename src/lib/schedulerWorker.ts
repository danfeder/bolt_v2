// Web Worker for handling scheduling computation
import BacktrackingScheduler from './scheduler';
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
}

self.onmessage = (e: MessageEvent<ScheduleRequest>) => {
  try {
    const scheduler = new BacktrackingScheduler({
      ...e.data,
      startDate: new Date(e.data.startDate),
      endDate: new Date(e.data.endDate)
    });

    // Send progress updates every 100ms
    let lastUpdate = Date.now();
    scheduler.onProgress = (progress) => {
      const now = Date.now();
      if (now - lastUpdate >= 100) {
        self.postMessage({ type: 'progress', progress });
        lastUpdate = now;
      }
    };

    const assignments = scheduler.solve();
    self.postMessage({ type: 'success', assignments });
  } catch (error) {
    self.postMessage({ 
      type: 'error', 
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};