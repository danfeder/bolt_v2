import { ScheduleRequest, ScheduleResult } from './types';
import { Class, ScheduleAssignment } from '../../src/types';
import { addDays, isSameDay, startOfWeek } from 'date-fns';

import { operations_research } from 'ts-ortools';

type MPSolver = operations_research.MPSolver;
type MPVariable = operations_research.MPVariable;
type MPObjective = operations_research.MPObjective;
type MPConstraint = operations_research.MPConstraint;

export async function createSchedule(request: ScheduleRequest): Promise<ScheduleResult> {
  const startTime = Date.now();
  
  try {
    const {
      classes,
      teacherAvailability,
      constraints: {
        maxClassesPerDay,
        maxClassesPerWeek,
        minPeriodsPerWeek,
        maxConsecutiveClasses,
        consecutiveClassesRule
      }
    } = request;

    // Create solver instance using operations_research.MPSolver
    const solver = new operations_research.MPSolver(
      'GymScheduler',
      operations_research.MPSolver.OptimizationProblemType.CBC_MIXED_INTEGER_PROGRAMMING
    );
    
    // Create binary variables for each possible assignment
    const variables = createScheduleVariables(solver, classes, request);
    
    // Add constraints
    addTimeSlotConstraints(solver, variables, request);
    addTeacherConstraints(solver, variables, request);
    addConsecutiveClassConstraints(solver, variables, request);
    addRequiredPeriodConstraints(solver, variables, request);
    
    // Set optimization objectives
    const objective = solver.MutableObjective();
    setOptimizationObjectives(objective, variables, request);
    objective.SetMinimization();
    
    // Solve the problem
    const resultStatus = solver.Solve();
    
    if (resultStatus !== operations_research.MPSolver.ResultStatus.OPTIMAL) {
      throw new Error('No optimal solution found');
    }

    // Convert solution to schedule assignments
    const assignments = convertSolutionToAssignments(variables, classes);
    
    // Calculate optimization score
    const score = calculateScore(assignments, request);
    
    return {
      assignments,
      duration: Date.now() - startTime,
      score
    };
  } catch (error) {
    console.error('OR-Tools scheduling error:', error);
    throw error;
  }
}

interface ScheduleVariable {
  variable: MPVariable;
  classId: string;
  date: Date;
  period: number;
}

function createScheduleVariables(
  solver: MPSolver,
  classes: Class[],
  request: ScheduleRequest
): ScheduleVariable[] {
  const variables: ScheduleVariable[] = [];
  const startDate = new Date(request.startDate);
  const endDate = new Date(request.endDate);

  for (const classObj of classes) {
    let currentDate = startDate;
    while (currentDate <= endDate) {
      if (currentDate.getDay() !== 0 && currentDate.getDay() !== 6) { // Skip weekends
        for (let period = 1; period <= 8; period++) {
          const varName = `class_${classObj.id}_${currentDate.toISOString()}_${period}`;
          variables.push({
            variable: solver.MakeBoolVar(varName),
            classId: classObj.id,
            date: new Date(currentDate),
            period
          });
        }
      }
      currentDate = addDays(currentDate, 1);
    }
  }
  
  return variables;
}

function addTimeSlotConstraints(
  solver: MPSolver,
  variables: ScheduleVariable[],
  request: ScheduleRequest
) {
  // Each class must be scheduled exactly once
  for (const classObj of request.classes) {
    const classVars = variables.filter(v => v.classId === classObj.id);
    const constraint = solver.MakeRowConstraint(1, 1);
    for (const v of classVars) {
      constraint.SetCoefficient(v.variable, 1);
    }
  }

  // Maximum classes per day constraint
  const byDate = groupVariablesByDate(variables);
  for (const [, dateVars] of byDate) {
    const constraint = solver.MakeRowConstraint(0, request.constraints.maxClassesPerDay);
    for (const v of dateVars) {
      constraint.SetCoefficient(v.variable, 1);
    }
  }

  // Maximum classes per week constraint
  const byWeek = groupVariablesByWeek(variables);
  for (const [, weekVars] of byWeek) {
    const constraint = solver.MakeRowConstraint(0, request.constraints.maxClassesPerWeek);
    for (const v of weekVars) {
      constraint.SetCoefficient(v.variable, 1);
    }
  }

  // Minimum periods per week constraint
  for (const classObj of request.classes) {
    const byWeek = groupVariablesByWeek(
      variables.filter(v => v.classId === classObj.id)
    );
    for (const [, weekVars] of byWeek) {
      if (weekVars.length > 0) { // Only add constraint if there are variables for this week
        const constraint = solver.MakeRowConstraint(
          request.constraints.minPeriodsPerWeek,
          request.constraints.maxClassesPerWeek
        );
        for (const v of weekVars) {
          constraint.SetCoefficient(v.variable, 1);
        }
      }
    }
  }
}

function addTeacherConstraints(
  solver: MPSolver,
  variables: ScheduleVariable[],
  request: ScheduleRequest
) {
  // Handle teacher unavailability
  for (const ta of request.teacherAvailability) {
    const date = new Date(ta.date);
    const dateVars = variables.filter(v => isSameDay(v.date, date));
    
    for (const slot of ta.unavailableSlots) {
      const constraint = solver.MakeRowConstraint(0, 0);
      const slotVars = dateVars.filter(v => v.period === slot.period);
      for (const v of slotVars) {
        constraint.SetCoefficient(v.variable, 1);
      }
    }
  }
}

function addConsecutiveClassConstraints(
  solver: MPSolver,
  variables: ScheduleVariable[],
  request: ScheduleRequest
) {
  if (request.constraints.consecutiveClassesRule === 'hard') {
    const byDate = groupVariablesByDate(variables);
    for (const [, dateVars] of byDate) {
      for (let period = 1; period <= 7; period++) {
        const constraint = solver.MakeRowConstraint(
          0,
          request.constraints.maxConsecutiveClasses
        );
        
        const consecutiveVars = dateVars.filter(
          v => v.period === period || v.period === period + 1
        );
        
        for (const v of consecutiveVars) {
          constraint.SetCoefficient(v.variable, 1);
        }
      }
    }
  }
}

function addRequiredPeriodConstraints(
  solver: MPSolver,
  variables: ScheduleVariable[],
  request: ScheduleRequest
) {
  for (const classObj of request.classes) {
    for (const req of classObj.weeklySchedule.requiredPeriods) {
      const matchingVars = variables.filter(
        v => v.classId === classObj.id &&
             v.date.getDay() === req.dayOfWeek &&
             v.period === req.period
      );
      
      if (matchingVars.length > 0) {
        const constraint = solver.MakeRowConstraint(1, 1);
        for (const v of matchingVars) {
          constraint.SetCoefficient(v.variable, 1);
        }
      }
    }
  }
}

function setOptimizationObjectives(
  objective: MPObjective,
  variables: ScheduleVariable[],
  request: ScheduleRequest
) {
  // Minimize total schedule duration
  for (const v of variables) {
    const daysFromStart = Math.floor(
      (v.date.getTime() - new Date(request.startDate).getTime()) / (1000 * 60 * 60 * 24)
    );
    objective.SetCoefficient(v.variable, daysFromStart);
  }
  
  // Prefer preferred periods
  for (const classObj of request.classes) {
    for (const pref of classObj.weeklySchedule.preferredPeriods) {
      const matchingVars = variables.filter(
        v => v.classId === classObj.id &&
             v.date.getDay() === pref.dayOfWeek &&
             v.period === pref.period
      );
      
      for (const v of matchingVars) {
        objective.SetCoefficient(v.variable, -10); // Negative to prefer these slots
      }
    }
  }
  
  // Avoid certain periods
  for (const classObj of request.classes) {
    for (const avoid of classObj.weeklySchedule.avoidPeriods) {
      const matchingVars = variables.filter(
        v => v.classId === classObj.id &&
             v.date.getDay() === avoid.dayOfWeek &&
             v.period === avoid.period
      );
      
      for (const v of matchingVars) {
        objective.SetCoefficient(v.variable, 5); // Positive to avoid these slots
      }
    }
  }
}

function convertSolutionToAssignments(
  variables: ScheduleVariable[],
  classes: Class[]
): ScheduleAssignment[] {
  return variables
    .filter(v => v.variable.solution_value() > 0.5)
    .map(v => ({
      classId: v.classId,
      date: v.date.toISOString(),
      timeSlot: {
        dayOfWeek: v.date.getDay(),
        period: v.period
      }
    }));
}

function calculateScore(assignments: ScheduleAssignment[], request: ScheduleRequest): number {
  let score = 0;
  
  // Calculate score based on various optimization criteria
  for (const assignment of assignments) {
    const classObj = request.classes.find(c => c.id === assignment.classId)!;
    const date = new Date(assignment.date);
    
    // Preferred periods
    if (classObj.weeklySchedule.preferredPeriods.some(
      p => p.dayOfWeek === assignment.timeSlot.dayOfWeek &&
          p.period === assignment.timeSlot.period
    )) {
      score += 10;
    }
    
    // Avoided periods
    if (classObj.weeklySchedule.avoidPeriods.some(
      p => p.dayOfWeek === assignment.timeSlot.dayOfWeek &&
          p.period === assignment.timeSlot.period
    )) {
      score -= 5;
    }
    
    // Schedule compactness
    const daysFromStart = Math.floor(
      (date.getTime() - new Date(request.startDate).getTime()) / (1000 * 60 * 60 * 24)
    );
    score -= daysFromStart;
  }
  
  return score;
}

function groupVariablesByDate(variables: ScheduleVariable[]): Map<string, ScheduleVariable[]> {
  const map = new Map<string, ScheduleVariable[]>();
  
  for (const v of variables) {
    const dateStr = v.date.toISOString().split('T')[0];
    const dateVars = map.get(dateStr) || [];
    dateVars.push(v);
    map.set(dateStr, dateVars);
  }
  
  return map;
}

function groupVariablesByWeek(variables: ScheduleVariable[]): Map<string, ScheduleVariable[]> {
  const map = new Map<string, ScheduleVariable[]>();
  
  for (const v of variables) {
    const weekStart = startOfWeek(v.date, { weekStartsOn: 1 }); // Start week on Monday
    const weekKey = weekStart.toISOString().split('T')[0];
    const weekVars = map.get(weekKey) || [];
    weekVars.push(v);
    map.set(weekKey, weekVars);
  }
  
  return map;
}
