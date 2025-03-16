import { useScheduleStore } from './scheduleStore';
import type { Priority, InstructorLoadSettings, AdvancedSettings } from '../components/simplifiedScheduler/types';
import type { SolverWeights, ScheduleConstraints } from '../types/index';

/**
 * Maps our simplified priorities to SolverWeights
 * Higher position in the array = higher priority = higher weight
 */
export const mapPrioritiesToWeights = (priorities: Priority[]): SolverWeights => {
  // Create a base weights object with default values
  const weights: SolverWeights = {
    distribution: 1000,
    daily_balance: 1000,
    day_usage: 1000,
    preferred_periods: 1000,
    avoid_periods: -1000,
    earlier_dates: 1000,
    final_week_compression: 1000
  };

  // Adjust weights based on priority order (higher in list = higher weight)
  priorities.forEach((priority, index) => {
    const priorityValue = 4000 - (index * 1000);
    
    // Map our priority IDs to the actual solver weight keys
    switch (priority.id) {
      case 'grade_grouping':
        // Grade grouping affects distribution and daily_balance
        weights.distribution = priorityValue;
        break;
      case 'weekly_balance':
        weights.day_usage = priorityValue;
        break;
      case 'daily_spacing':
        weights.daily_balance = priorityValue;
        break;
      case 'preferred_periods':
        weights.preferred_periods = priorityValue;
        // Avoid periods should match the preferred_periods priority but negative
        weights.avoid_periods = -priorityValue;
        break;
    }
  });

  return weights;
};

/**
 * Maps instructor load settings to ScheduleConstraints
 * Preserves other constraint values from the current constraints
 */
export const mapInstructorLoadToConstraints = (
  loadSettings: InstructorLoadSettings, 
  currentConstraints: ScheduleConstraints
): Partial<ScheduleConstraints> => {
  return {
    maxClassesPerDay: loadSettings.maxPerDay,
    maxClassesPerWeek: loadSettings.maxPerWeek,
    minPeriodsPerWeek: loadSettings.minPerWeek,
    // Copy the max consecutive classes from current constraints, but override the rule type
    maxConsecutiveClasses: currentConstraints.maxConsecutiveClasses,
    consecutiveClassesRule: loadSettings.allowMaxFlexibility ? 'soft' : 'hard',
    // Preserve date range
    startDate: currentConstraints.startDate,
    endDate: currentConstraints.endDate
  };
};

/**
 * Hook that provides simplified access to the schedule store
 * Maps our simplified UI model to the existing store structure
 */
export const useSimplifiedScheduler = () => {
  const store = useScheduleStore();
  
  // Current state
  const isGenerating = store.isGenerating;
  const error = store.error;
  const constraints = store.constraints;
  
  // Generate schedule with our simplified config
  const generateSchedule = async (
    priorities: Priority[],
    instructorLoad: InstructorLoadSettings,
    advanced: AdvancedSettings
  ) => {
    // Map our simplified config to the store's expected format
    const weights = mapPrioritiesToWeights(priorities);
    const updatedConstraints = mapInstructorLoadToConstraints(instructorLoad, constraints);
    
    // Apply advanced settings
    // In future increments, we'll integrate this more deeply with the solver
    if (advanced.requireBreakBetweenClasses) {
      // Ensure there's a break between classes by setting max consecutive to 1
      updatedConstraints.maxConsecutiveClasses = 1;
    }
    
    // Auto-tuning will be implemented in a future increment
    if (advanced.autoTuneWeights) {
      console.log('Auto-tuning enabled, will be implemented in future increment');
    }
    
    // Update store with our mapped values
    store.setConstraints(updatedConstraints);
    
    // TODO: In the future, extend the store to accept weights directly
    // For now, weights are calculated but not used (will be added in next increment)
    console.log('Applied weights from priority order:', weights);
    
    // Generate the schedule
    await store.generateSchedule();
  };
  
  return {
    isGenerating,
    error,
    constraints,
    generateSchedule
  };
};
