import { create, StateCreator } from 'zustand';
import { addDays } from 'date-fns';
import type { 
  Class, 
  ScheduleAssignment, 
  ScheduleConstraints, 
  InstructorAvailability,
  ScheduleMetadata,
  SchedulerTab,
  TabState,
  TabValidationState,
  GeneticSolverConfig
} from '../types';
import type { ComparisonResult } from './types';
import { analyzeScheduleComplexity, type SolverDecision } from '../lib/scheduleComplexity';
import { generateScheduleWithOrTools, compareScheduleSolvers } from '../lib/apiClient';

const defaultGeneticConfig: GeneticSolverConfig = {
  enabled: false,
  populationSize: 100,
  eliteSize: 2,
  mutationRate: 0.1,
  crossoverRate: 0.8,
  maxGenerations: 100
};

interface ScheduleState extends TabState {
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
  geneticConfig: GeneticSolverConfig;
  tabValidation: TabValidationState;
  setClasses: (classes: Class[]) => void;
  setCurrentTab: (tab: SchedulerTab) => void;
  validateTab: (tab: SchedulerTab) => boolean;
  markTabComplete: (tab: SchedulerTab) => void;
  setInstructorAvailability: (availability: InstructorAvailability[] | ((prev: InstructorAvailability[]) => InstructorAvailability[])) => void;
  setConstraints: (constraints: Partial<ScheduleConstraints>) => void;
  setSchedulerVersion: (version: 'stable' | 'dev') => void;
  setGeneticConfig: (config: Partial<GeneticSolverConfig>) => void;
  generateSchedule: () => Promise<void>;
  compareVersions: () => Promise<void>;
  cancelGeneration: () => void;
  clearError: () => void;
}

const defaultTabValidation: TabValidationState = {
  setup: false,
  visualize: false,
  debug: false
};

const defaultConstraints: ScheduleConstraints = {
  maxClassesPerDay: 4,
  maxClassesPerWeek: 16,
  minPeriodsPerWeek: 8,
  maxConsecutiveClasses: 1,
  consecutiveClassesRule: 'soft',
  startDate: new Date().toISOString(),
  endDate: addDays(new Date(), 30).toISOString()
};

export const useScheduleStore = create<ScheduleState>((
  set: (
    partial: ScheduleState | Partial<ScheduleState> | ((state: ScheduleState) => ScheduleState | Partial<ScheduleState>),
    replace?: boolean
  ) => void,
  get: () => ScheduleState
) => {
  const validateTab = (tab: SchedulerTab): boolean => {
    const state = get();
    switch (tab) {
      case 'setup':
        return state.classes.length > 0 && state.instructorAvailability.length > 0;
      case 'visualize':
        return state.assignments.length > 0;
      case 'debug':
        return state.lastGenerationMetadata !== null;
      default:
        return false;
    }
  };

  let worker: Worker | null = null;

  return {
    classes: [],
    instructorAvailability: [],
    currentTab: 'setup' as SchedulerTab,
    setupComplete: false,
    visualizationReady: false,
    tabValidation: defaultTabValidation,
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
    geneticConfig: defaultGeneticConfig,
    
    setClasses: (classes: Class[]) => set({ classes }),
    
    setInstructorAvailability: (availability: InstructorAvailability[] | ((prev: InstructorAvailability[]) => InstructorAvailability[])) => 
      set((state: ScheduleState) => ({ 
        instructorAvailability: typeof availability === 'function' 
          ? availability(state.instructorAvailability)
          : availability 
      })),
    
    setConstraints: (newConstraints: Partial<ScheduleConstraints>) => 
      set((state: ScheduleState) => ({
        constraints: { ...state.constraints, ...newConstraints }
      })),

    setGeneticConfig: (config: Partial<GeneticSolverConfig>) => 
      set((state: ScheduleState) => ({
        geneticConfig: { ...state.geneticConfig, ...config }
      })),

    setSchedulerVersion: (version: 'stable' | 'dev') => set({ schedulerVersion: version }),
    
    generateSchedule: async () => {
      const { classes, instructorAvailability, constraints, schedulerVersion, geneticConfig } = get();
      
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
          schedulerVersion,
          geneticConfig
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

    clearError: () => set({ error: null }),

    setCurrentTab: (tab: SchedulerTab) => {
      const isValid = validateTab(tab);
      set({ 
        currentTab: tab,
        tabValidation: {
          ...get().tabValidation,
          [tab]: isValid
        }
      });
    },

    validateTab,

    markTabComplete: (tab: SchedulerTab) => {
      const isValid = validateTab(tab);
      set((state: ScheduleState) => ({
        tabValidation: {
          ...state.tabValidation,
          [tab]: isValid
        },
        setupComplete: tab === 'setup' ? isValid : state.setupComplete,
        visualizationReady: tab === 'visualize' ? isValid : state.visualizationReady
      }));
    }
  };
});
