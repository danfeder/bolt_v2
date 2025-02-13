import { create } from 'zustand';
import { addDays } from 'date-fns';
import type { 
  Class, 
  ScheduleAssignment, 
  ScheduleConstraints, 
  InstructorAvailability,
  ScheduleMetadata 
} from '../types';
import type { ComparisonResult } from './types';
import { analyzeScheduleComplexity, type SolverDecision } from '../lib/scheduleComplexity';
import { generateScheduleWithOrTools, compareScheduleSolvers } from '../lib/apiClient';

interface ScheduleState {
  classes: Class[];
  instructorAvailability: InstructorAvailability[];
  assignments: ScheduleAssignment[];
  constraints: ScheduleConstraints;
  isGenerating: boolean;
  generationProgress: number;
  solverDecision: SolverDecision | null;
  schedulerVersion: 'stable' | 'dev';
  lastGenerationMetadata: ScheduleMetadata | null;
  comparisonResult: ComparisonResult | null;
  isComparing: boolean;
  error: string | null;
  setClasses: (classes: Class[]) => void;
  setInstructorAvailability: (availability: InstructorAvailability[] | ((prev: InstructorAvailability[]) => InstructorAvailability[])) => void;
  setConstraints: (constraints: Partial<ScheduleConstraints>) => void;
  setSchedulerVersion: (version: 'stable' | 'dev') => void;
  generateSchedule: () => Promise<void>;
  compareVersions: () => Promise<void>;
  cancelGeneration: () => void;
  clearError: () => void;
}

const defaultConstraints: ScheduleConstraints = {
  maxClassesPerDay: 4,
  maxClassesPerWeek: 16,
  minPeriodsPerWeek: 8,
  maxConsecutiveClasses: 1,
  consecutiveClassesRule: 'soft',
  startDate: new Date().toISOString(),
  endDate: addDays(new Date(), 30).toISOString()
};

export const useScheduleStore = create<ScheduleState>((set, get) => {
  let worker: Worker | null = null;

  return {
    classes: [],
    instructorAvailability: [],
    assignments: [],
    constraints: defaultConstraints,
    isGenerating: false,
    generationProgress: 0,
    solverDecision: null,
    schedulerVersion: 'stable',
    lastGenerationMetadata: null,
    comparisonResult: null,
    isComparing: false,
    error: null,
    
    setClasses: (classes: Class[]) => set({ classes }),
    
    setInstructorAvailability: (availability: InstructorAvailability[] | ((prev: InstructorAvailability[]) => InstructorAvailability[])) => 
      set((state) => ({ 
        instructorAvailability: typeof availability === 'function' 
          ? availability(state.instructorAvailability)
          : availability 
      })),
    
    setConstraints: (newConstraints: Partial<ScheduleConstraints>) => 
      set((state) => ({
        constraints: { ...state.constraints, ...newConstraints }
      })),

    setSchedulerVersion: (version: 'stable' | 'dev') => set({ schedulerVersion: version }),
    
    generateSchedule: async () => {
      const { classes, instructorAvailability, constraints, schedulerVersion } = get();
      
      if (classes.length === 0) {
        set({ error: 'No classes to schedule. Please add classes first.' });
        return;
      }

      if (constraints.minPeriodsPerWeek > constraints.maxClassesPerWeek) {
        set({ error: 'Minimum periods per week cannot be greater than maximum classes per week.' });
        return;
      }

      // Clear any previous errors
      set({ error: null });

      // Analyze schedule complexity and choose solver
      const decision = analyzeScheduleComplexity(classes, instructorAvailability, constraints);
      set({ solverDecision: decision });

      set({ isGenerating: true, generationProgress: 0 });

      try {
        // Use Python backend solver via API
        const result = await generateScheduleWithOrTools(
          classes,
          instructorAvailability,
          constraints,
          schedulerVersion
        );

        set({
          assignments: result.assignments,
          lastGenerationMetadata: result.metadata,
          isGenerating: false,
          generationProgress: 100,
          error: null
        });
      } catch (error) {
        set({ 
          isGenerating: false, 
          generationProgress: 0,
          error: error instanceof Error ? error.message : 'Failed to generate schedule'
        });
        throw error;
      }
    },

    compareVersions: async () => {
      const { classes, instructorAvailability, constraints } = get();
      
      if (classes.length === 0) {
        set({ error: 'No classes to schedule. Please add classes first.' });
        return;
      }

      // Clear any previous errors
      set({ error: null, isComparing: true });

      try {
        const result = await compareScheduleSolvers(
          classes,
          instructorAvailability,
          constraints
        );

        set({
          comparisonResult: result,
          isComparing: false,
          error: null
        });
      } catch (error) {
        set({ 
          isComparing: false,
          error: error instanceof Error ? error.message : 'Failed to compare solvers'
        });
        throw error;
      }
    },

    cancelGeneration: () => {
      if (worker) {
        worker.terminate();
        worker = null;
        set({ isGenerating: false, generationProgress: 0 });
      }
    },

    clearError: () => set({ error: null })
  };
});
