export interface TimeSlot {
  dayOfWeek: number;  // 1-5 (Monday-Friday)
  period: number;     // 1-8 (school periods)
}

export interface WeeklySchedule {
  conflicts: TimeSlot[];         // Recurring weekly conflicts
  preferredPeriods: TimeSlot[];  // Preferred time slots
  requiredPeriods: TimeSlot[];   // Required time slots - class MUST be scheduled in one of these
  avoidPeriods: TimeSlot[];      // Periods to avoid if possible
}

export interface Class {
  id: string;           // e.g., "1-409"
  name: string;         // e.g., "1-409"
  grade: string;        // Pre-K through 5
  weeklySchedule: WeeklySchedule;
}

export interface TeacherAvailability {
  date: string;         // ISO date string
  unavailableSlots: TimeSlot[];
  preferredSlots: TimeSlot[];
  avoidSlots: TimeSlot[];
}

export interface ScheduleAssignment {
  classId: string;
  date: string;        // ISO date string
  timeSlot: TimeSlot;
}

export interface ScheduleConstraints {
  maxClassesPerDay: number;
  maxClassesPerWeek: number;
  minPeriodsPerWeek: number;  // New constraint
  maxConsecutiveClasses: 1 | 2;
  consecutiveClassesRule: 'hard' | 'soft';
  startDate: string;    // ISO date string
  endDate: string;      // ISO date string
}