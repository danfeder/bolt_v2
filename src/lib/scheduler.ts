import { Class, ScheduleAssignment, TeacherAvailability } from '../types';
import { generateScheduleWithOrTools } from './apiClient';

interface SchedulerParams {
  classes: Class[];
  teacherAvailability: TeacherAvailability[];
  startDate: Date;
  endDate: Date;
  maxClassesPerDay: number;
  maxClassesPerWeek: number;
  minPeriodsPerWeek: number;
  maxConsecutiveClasses: 1 | 2;
  consecutiveClassesRule: 'hard' | 'soft';
}

/**
 * Frontend scheduler interface that uses the OR-Tools CP-SAT solver backend
 */
class Scheduler {
  private classes: Class[];
  private teacherAvailability: TeacherAvailability[];
  private startDate: Date;
  private endDate: Date;
  private maxClassesPerDay: number;
  private maxClassesPerWeek: number;
  private minPeriodsPerWeek: number;
  private maxConsecutiveClasses: 1 | 2;
  private consecutiveClassesRule: 'hard' | 'soft';
  
  constructor(params: SchedulerParams) {
    this.classes = params.classes;
    this.teacherAvailability = params.teacherAvailability;
    this.startDate = params.startDate;
    this.endDate = params.endDate;
    this.maxClassesPerDay = params.maxClassesPerDay;
    this.maxClassesPerWeek = params.maxClassesPerWeek;
    this.minPeriodsPerWeek = params.minPeriodsPerWeek;
    this.maxConsecutiveClasses = params.maxConsecutiveClasses;
    this.consecutiveClassesRule = params.consecutiveClassesRule;
  }

  async solve(version: 'stable' | 'dev' = 'stable'): Promise<ScheduleAssignment[]> {
    const response = await generateScheduleWithOrTools(
      this.classes,
      this.teacherAvailability,
      {
        startDate: this.startDate.toISOString(),
        endDate: this.endDate.toISOString(),
        maxClassesPerDay: this.maxClassesPerDay,
        maxClassesPerWeek: this.maxClassesPerWeek,
        minPeriodsPerWeek: this.minPeriodsPerWeek,
        maxConsecutiveClasses: this.maxConsecutiveClasses,
        consecutiveClassesRule: this.consecutiveClassesRule
      },
      version
    );

    return response.assignments;
  }
}

export default Scheduler;
