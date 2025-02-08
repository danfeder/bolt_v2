import { Class, TimeSlot, ScheduleAssignment, TeacherAvailability } from '../types';
import { addDays, isSameDay, isWithinInterval, startOfWeek, endOfWeek, startOfDay, format } from 'date-fns';

interface ScheduleParams {
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

class BacktrackingScheduler {
  private classes: Class[];
  private teacherAvailability: TeacherAvailability[];
  private startDate: Date;
  private endDate: Date;
  private maxClassesPerDay: number;
  private maxClassesPerWeek: number;
  private minPeriodsPerWeek: number;
  private maxConsecutiveClasses: 1 | 2;
  private consecutiveClassesRule: 'hard' | 'soft';
  private assignments: ScheduleAssignment[] = [];
  private dates: Date[] = [];
  
  // Cache for performance optimization
  private dailyAssignmentCounts = new Map<string, number>();
  private weeklyAssignmentCounts = new Map<string, number>();
  private validSlotCache = new Map<string, Array<{ date: Date; period: number }>>();
  private dateStrings = new Map<Date, string>();
  
  onProgress?: (progress: number) => void;
  private totalAttempts = 0;
  private maxAttempts = 5000000; // Increased max attempts
  private lastProgressUpdate = 0;
  private progressUpdateInterval = 100; // ms

  constructor(params: ScheduleParams) {
    this.classes = this.orderClassesByConstraints(params.classes);
    this.teacherAvailability = params.teacherAvailability;
    this.startDate = startOfDay(params.startDate);
    this.endDate = startOfDay(params.endDate);
    this.maxClassesPerDay = params.maxClassesPerDay;
    this.maxClassesPerWeek = params.maxClassesPerWeek;
    this.minPeriodsPerWeek = params.minPeriodsPerWeek;
    this.maxConsecutiveClasses = params.maxConsecutiveClasses;
    this.consecutiveClassesRule = params.consecutiveClassesRule;
    
    this.initializeDates();
    this.validateConstraints(); // Validate constraints immediately
  }

  private initializeDates() {
    this.dates = [];
    let currentDate = this.startDate;
    while (currentDate <= this.endDate) {
      if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) {
        this.dates.push(currentDate);
        this.dateStrings.set(currentDate, currentDate.toISOString().split('T')[0]);
      }
      currentDate = addDays(currentDate, 1);
    }
  }

  private validateConstraints() {
    if (this.maxClassesPerDay < 1 || this.maxClassesPerDay > 8) {
      throw new Error('Maximum classes per day must be between 1 and 8');
    }

    // Calculate minimum days needed based on total classes and max classes per day
    const totalClasses = this.classes.length;
    const minDaysNeeded = Math.ceil(totalClasses / this.maxClassesPerDay);
    const availableDays = this.dates.length;

    if (minDaysNeeded > availableDays) {
      throw new Error(
        `Schedule impossible: need at least ${minDaysNeeded} days to schedule ` +
        `${totalClasses} classes with max ${this.maxClassesPerDay} classes per day, ` +
        `but only have ${availableDays} days available. Try:\n` +
        `1. Increasing maximum classes per day (currently ${this.maxClassesPerDay})\n` +
        `2. Extending the schedule date range`
      );
    }

    // Calculate minimum weeks needed based on total classes and max classes per week
    const totalWeeks = Math.ceil(availableDays / 5);
    const minClassesPerWeek = Math.ceil(totalClasses / totalWeeks);
    
    if (minClassesPerWeek > this.maxClassesPerWeek) {
      throw new Error(
        `Schedule impossible: need to schedule ${totalClasses} classes over ` +
        `${totalWeeks} weeks (${minClassesPerWeek} classes per week), but max is ` +
        `${this.maxClassesPerWeek} classes per week. Try:\n` +
        `1. Increasing maximum classes per week (currently ${this.maxClassesPerWeek})\n` +
        `2. Extending the schedule date range`
      );
    }
  }

  solve(): ScheduleAssignment[] {
    this.assignments = [];
    this.dailyAssignmentCounts.clear();
    this.weeklyAssignmentCounts.clear();
    this.validSlotCache.clear();
    this.totalAttempts = 0;
    this.lastProgressUpdate = Date.now();

    if (!this.backtrack(0)) {
      throw new Error(
        'Unable to find a valid schedule that meets all constraints. Try:\n' +
        '1. Increasing the maximum classes per day\n' +
        '2. Extending the date range\n' +
        '3. Checking for conflicting constraints'
      );
    }

    // Verify final schedule meets all constraints
    this.verifySchedule();

    return this.assignments;
  }

  private backtrack(classIndex: number): boolean {
    this.totalAttempts++;
    
    if (this.totalAttempts > this.maxAttempts) {
      return false;
    }

    // Update progress less frequently
    const now = Date.now();
    if (now - this.lastProgressUpdate >= this.progressUpdateInterval) {
      if (this.onProgress) {
        const progress = (classIndex / this.classes.length) * 100;
        this.onProgress(Math.min(progress, 99));
      }
      this.lastProgressUpdate = now;
    }

    if (classIndex >= this.classes.length) {
      return true;
    }

    const classObj = this.classes[classIndex];
    const slots = this.getValidTimeSlots(classObj);
    
    // Randomize slot order to avoid getting stuck
    for (let i = slots.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [slots[i], slots[j]] = [slots[j], slots[i]];
    }

    for (const slot of slots) {
      if (!this.canAssignSlot(slot, classObj)) {
        continue;
      }

      const assignment = this.createAssignment(slot, classObj);
      this.applyAssignment(assignment);

      if (this.backtrack(classIndex + 1)) {
        return true;
      }

      this.removeAssignment(assignment);
    }

    return false;
  }

  private canAssignSlot(slot: { date: Date; period: number }, classObj: Class): boolean {
    const dateStr = this.dateStrings.get(slot.date)!;
    const weekStr = startOfWeek(slot.date, { weekStartsOn: 1 }).toISOString();
    
    // Check daily and weekly limits
    const dailyCount = (this.dailyAssignmentCounts.get(dateStr) || 0);
    if (dailyCount >= this.maxClassesPerDay) {
      return false;
    }

    const weeklyCount = (this.weeklyAssignmentCounts.get(weekStr) || 0);
    if (weeklyCount >= this.maxClassesPerWeek) {
      return false;
    }

    // Check consecutive classes constraint
    if (this.consecutiveClassesRule === 'hard') {
      const hasConsecutive = this.assignments.some(a => {
        if (!isSameDay(new Date(a.date), slot.date)) {
          return false;
        }
        return Math.abs(a.timeSlot.period - slot.period) <= 1;
      });

      if (hasConsecutive) {
        return false;
      }
    }

    return true;
  }

  private createAssignment(slot: { date: Date; period: number }, classObj: Class): ScheduleAssignment {
    return {
      classId: classObj.id,
      date: slot.date.toISOString(),
      timeSlot: {
        dayOfWeek: slot.date.getDay(),
        period: slot.period
      }
    };
  }

  private applyAssignment(assignment: ScheduleAssignment) {
    const date = new Date(assignment.date);
    const dateStr = this.dateStrings.get(date)!;
    const weekStr = startOfWeek(date, { weekStartsOn: 1 }).toISOString();
    
    this.assignments.push(assignment);
    this.dailyAssignmentCounts.set(
      dateStr,
      (this.dailyAssignmentCounts.get(dateStr) || 0) + 1
    );
    this.weeklyAssignmentCounts.set(
      weekStr,
      (this.weeklyAssignmentCounts.get(weekStr) || 0) + 1
    );
  }

  private removeAssignment(assignment: ScheduleAssignment) {
    const date = new Date(assignment.date);
    const dateStr = this.dateStrings.get(date)!;
    const weekStr = startOfWeek(date, { weekStartsOn: 1 }).toISOString();
    
    this.assignments.pop();
    this.dailyAssignmentCounts.set(
      dateStr,
      (this.dailyAssignmentCounts.get(dateStr) || 1) - 1
    );
    this.weeklyAssignmentCounts.set(
      weekStr,
      (this.weeklyAssignmentCounts.get(weekStr) || 1) - 1
    );
  }

  private getValidTimeSlots(classObj: Class): Array<{ date: Date; period: number }> {
    const cacheKey = classObj.id;
    if (this.validSlotCache.has(cacheKey)) {
      return this.validSlotCache.get(cacheKey)!;
    }

    const validSlots: Array<{ date: Date; period: number }> = [];
    const conflicts = new Set(
      classObj.weeklySchedule.conflicts.map(c => `${c.dayOfWeek}-${c.period}`)
    );

    for (const date of this.dates) {
      const dayOfWeek = date.getDay();
      
      // Check teacher availability
      const teacherDay = this.teacherAvailability.find(ta => 
        isSameDay(new Date(ta.date), date)
      );

      for (let period = 1; period <= 8; period++) {
        // Skip if it's a conflict period
        if (conflicts.has(`${dayOfWeek}-${period}`)) continue;

        // Skip if teacher is unavailable
        const teacherUnavailable = teacherDay?.unavailableSlots.some(
          slot => slot.period === period
        );
        if (teacherUnavailable) continue;

        validSlots.push({ date, period });
      }
    }

    // Sort slots by preference
    const sortedSlots = this.sortSlotsByPreference(classObj, validSlots);
    this.validSlotCache.set(cacheKey, sortedSlots);
    return sortedSlots;
  }

  private sortSlotsByPreference(
    classObj: Class, 
    slots: Array<{ date: Date; period: number }>
  ): Array<{ date: Date; period: number }> {
    const preferredPeriods = new Set(
      classObj.weeklySchedule.preferredPeriods.map(p => `${p.dayOfWeek}-${p.period}`)
    );
    const requiredPeriods = new Set(
      classObj.weeklySchedule.requiredPeriods.map(r => `${r.dayOfWeek}-${r.period}`)
    );
    const avoidPeriods = new Set(
      classObj.weeklySchedule.avoidPeriods.map(a => `${a.dayOfWeek}-${a.period}`)
    );

    return slots.sort((a, b) => {
      const scoreA = this.getSlotScore(a.date, a.period, preferredPeriods, requiredPeriods, avoidPeriods);
      const scoreB = this.getSlotScore(b.date, b.period, preferredPeriods, requiredPeriods, avoidPeriods);
      return scoreB - scoreA;
    });
  }

  private getSlotScore(
    date: Date, 
    period: number,
    preferredPeriods: Set<string>,
    requiredPeriods: Set<string>,
    avoidPeriods: Set<string>
  ): number {
    const dayOfWeek = date.getDay();
    const key = `${dayOfWeek}-${period}`;
    
    let score = 0;
    
    if (requiredPeriods.has(key)) score += 1000;
    if (preferredPeriods.has(key)) score += 100;
    if (avoidPeriods.has(key)) score -= 50;
    
    // Prefer earlier dates and periods
    score -= Math.floor((date.getTime() - this.startDate.getTime()) / (24 * 60 * 60 * 1000)) * 0.1;
    score -= period * 0.1;
    
    return score;
  }

  private orderClassesByConstraints(classes: Class[]): Class[] {
    return [...classes].sort((a, b) => {
      const aConstraints = 
        a.weeklySchedule.conflicts.length + 
        a.weeklySchedule.preferredPeriods.length + 
        a.weeklySchedule.requiredPeriods.length +
        a.weeklySchedule.avoidPeriods.length;
      const bConstraints = 
        b.weeklySchedule.conflicts.length + 
        b.weeklySchedule.preferredPeriods.length + 
        b.weeklySchedule.requiredPeriods.length +
        b.weeklySchedule.avoidPeriods.length;
      return bConstraints - aConstraints;
    });
  }

  private verifySchedule(): void {
    // Get all unique dates from assignments
    const assignmentsByDate = new Map<string, ScheduleAssignment[]>();
    
    for (const assignment of this.assignments) {
      const date = format(new Date(assignment.date), 'yyyy-MM-dd');
      const dayAssignments = assignmentsByDate.get(date) || [];
      dayAssignments.push(assignment);
      assignmentsByDate.set(date, dayAssignments);
    }

    // Verify daily limits
    for (const [date, assignments] of assignmentsByDate) {
      if (assignments.length > this.maxClassesPerDay) {
        throw new Error(
          `Schedule validation failed: ${date} has ${assignments.length} classes, ` +
          `exceeding maximum of ${this.maxClassesPerDay}`
        );
      }
    }

    // Verify weekly limits
    const assignmentsByWeek = new Map<string, ScheduleAssignment[]>();
    
    for (const assignment of this.assignments) {
      const date = new Date(assignment.date);
      const weekStart = format(startOfWeek(date, { weekStartsOn: 1 }), 'yyyy-MM-dd');
      const weekAssignments = assignmentsByWeek.get(weekStart) || [];
      weekAssignments.push(assignment);
      assignmentsByWeek.set(weekStart, weekAssignments);
    }

    for (const [weekStart, assignments] of assignmentsByWeek) {
      if (assignments.length > this.maxClassesPerWeek) {
        throw new Error(
          `Schedule validation failed: Week of ${weekStart} has ${assignments.length} classes, ` +
          `exceeding maximum of ${this.maxClassesPerWeek}`
        );
      }
    }

    // Verify consecutive classes constraint if it's a hard constraint
    if (this.consecutiveClassesRule === 'hard') {
      for (const [date, assignments] of assignmentsByDate) {
        // Sort assignments by period
        assignments.sort((a, b) => a.timeSlot.period - b.timeSlot.period);
        
        // Check for consecutive periods
        for (let i = 0; i < assignments.length - 1; i++) {
          const consecutive = assignments.filter(a => 
            Math.abs(a.timeSlot.period - assignments[i].timeSlot.period) <= 1
          ).length;

          if (consecutive > this.maxConsecutiveClasses) {
            throw new Error(
              `Schedule validation failed: Found ${consecutive} consecutive classes ` +
              `on ${date}, exceeding maximum of ${this.maxConsecutiveClasses}`
            );
          }
        }
      }
    }

    // Verify all classes are scheduled exactly once
    const scheduledClasses = new Set(this.assignments.map(a => a.classId));
    const allClasses = new Set(this.classes.map(c => c.id));

    if (scheduledClasses.size !== allClasses.size) {
      throw new Error(
        'Schedule validation failed: Not all classes were scheduled exactly once'
      );
    }

    for (const classId of allClasses) {
      const classAssignments = this.assignments.filter(a => a.classId === classId);
      if (classAssignments.length !== 1) {
        throw new Error(
          `Schedule validation failed: Class ${classId} was scheduled ` +
          `${classAssignments.length} times instead of exactly once`
        );
      }
    }
  }
}

export default BacktrackingScheduler;