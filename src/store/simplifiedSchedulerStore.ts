import { useScheduleStore } from './scheduleStore';
import { create } from 'zustand';
import { apiClient } from '../lib/apiClient';
import type { Priority, InstructorLoadSettings, AdvancedSettings, ConstraintValidationResult } from '../components/simplifiedScheduler/types';
import type { SolverWeights, ScheduleConstraints, ConstraintCategory } from '../types/index';

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
  currentConstraints: ScheduleConstraints,
  advanced?: AdvancedSettings
): Partial<ScheduleConstraints> => {
  return {
    maxClassesPerDay: loadSettings.maxPerDay,
    maxClassesPerWeek: loadSettings.maxPerWeek,
    minPeriodsPerWeek: loadSettings.minPerWeek,
    // Copy the max consecutive classes from current constraints, but override the rule type
    maxConsecutiveClasses: currentConstraints.maxConsecutiveClasses,
    consecutiveClassesRule: loadSettings.allowMaxFlexibility ? 'soft' : 'hard',
    // Use start date from advanced settings if available, otherwise preserve current
    // Convert Date to ISO string format for the API
    startDate: advanced?.startDate ? advanced.startDate.toISOString().split('T')[0] : currentConstraints.startDate,
    endDate: currentConstraints.endDate
  };
};

// Define the simplified scheduler store for constraint categories
interface ConstraintCategoryState {
  // Data
  constraintCategories: ConstraintCategory[];
  validationResult: ConstraintValidationResult | null;
  loadingCategories: boolean;
  errorMessage: string | null;
  
  // Actions
  fetchConstraintCategories: () => Promise<void>;
  validateConstraintCompatibility: (priorities: Priority[], advanced: AdvancedSettings) => Promise<ConstraintValidationResult>;
  mapPriorityToConstraints: (priority: Priority) => string[];
}

// Create a store for managing constraint categories and validation
export const useConstraintCategoryStore = create<ConstraintCategoryState>((set, get) => ({
  constraintCategories: [],
  validationResult: null,
  loadingCategories: false,
  errorMessage: null,
  
  fetchConstraintCategories: async () => {
    try {
      set({ loadingCategories: true, errorMessage: null });
      const categories = await apiClient.getConstraintCategories();
      set({ constraintCategories: categories, loadingCategories: false });
    } catch (error) {
      console.error('Error fetching constraint categories:', error);
      set({ 
        errorMessage: error instanceof Error ? error.message : 'Failed to fetch constraint categories', 
        loadingCategories: false 
      });
    }
  },
  
  validateConstraintCompatibility: async (priorities: Priority[], advanced: AdvancedSettings) => {
    // This would call the backend API to validate constraints when implemented
    // For now, we'll simulate validation locally
    const result: ConstraintValidationResult = {
      isValid: true,
      messages: []
    };
    
    // Get all constraint IDs from priorities
    const enabledConstraints = priorities.flatMap(p => 
      p.constraintIds ? p.constraintIds : []
    );
    
    // Apply validation logic based on enabled categories from advanced settings
    if (advanced.strictValidation && advanced.enabledCategories.length > 0) {
      // This is a placeholder for the actual validation logic
      // In a future increment, we'll call the backend API for validation
      console.log('Validating constraints:', enabledConstraints);
    }
    
    // TODO: Replace with actual API call once backend endpoint is available
    // Simulate validation for now
    set({ validationResult: result });
    return result;
  },
  
  mapPriorityToConstraints: (priority: Priority) => {
    const { constraintCategories } = get();
    
    // Find constraints in the appropriate category
    if (priority.constraintCategory && priority.constraintCategory !== '') {
      const category = constraintCategories.find(c => c.name === priority.constraintCategory);
      if (category) {
        return category.constraints.map(c => c.name);
      }
    }
    
    // Default constraint mapping if category doesn't exist or no category specified
    switch (priority.id) {
      case 'grade_grouping':
        return ['distribution_constraint', 'grade_balance_constraint'];
      case 'weekly_balance':
        return ['weekly_distribution_constraint'];
      case 'daily_spacing':
        return ['daily_spacing_constraint'];
      case 'preferred_periods':
        return ['preferred_period_constraint'];
      default:
        return [];
    }
  }
}));

/**
 * Hook that provides simplified access to the schedule store
 * Maps our simplified UI model to the existing store structure
 */
export const useSimplifiedScheduler = () => {
  const store = useScheduleStore();
  const constraintStore = useConstraintCategoryStore();
  
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
    // Validate required parameters first
    if (!advanced.startDate) {
      throw new Error('Start date is required for scheduling. Please select a start date in Advanced Options.');
    }
    
    // First validate constraint compatibility if strict validation is enabled
    if (advanced.strictValidation) {
      const validationResult = await constraintStore.validateConstraintCompatibility(priorities, advanced);
      if (!validationResult.isValid && !advanced.relaxIncompatibleConstraints) {
        throw new Error(`Constraint validation failed: ${validationResult.messages.join(', ')}`);
      }
    }

    // Map our simplified config to the store's expected format
    const weights = mapPrioritiesToWeights(priorities);
    const updatedConstraints = mapInstructorLoadToConstraints(instructorLoad, constraints, advanced);
    
    // Apply advanced settings
    if (advanced.requireBreakBetweenClasses) {
      // Ensure there's a break between classes by setting max consecutive to 1
      updatedConstraints.maxConsecutiveClasses = 1;
    }
    
    // Auto-tuning connects with relaxable constraints
    if (advanced.autoTuneWeights) {
      // In the enhanced constraint system, auto-tuning uses relaxable constraints
      // This will be fully implemented in the next increment
      console.log('Auto-tuning using relaxable constraints will be implemented next');
    }
    
    // Update store with our mapped values
    store.setConstraints(updatedConstraints);
    
    // Apply weights to the store - this will be wired up to the actual API
    // that accepts weights for the enhanced constraint system
    console.log('Applied weights from priority order:', weights);
    
    // Generate the schedule
    await store.generateSchedule();
  };
  
  return {
    // Schedule store properties
    isGenerating,
    error,
    constraints,
    
    // Constraint category features
    constraintCategories: constraintStore.constraintCategories,
    loadingCategories: constraintStore.loadingCategories,
    validationResult: constraintStore.validationResult,
    fetchConstraintCategories: constraintStore.fetchConstraintCategories,
    validateConstraints: constraintStore.validateConstraintCompatibility,
    mapPriorityToConstraints: constraintStore.mapPriorityToConstraints,
    
    // Core functionality
    generateSchedule
  };
};
