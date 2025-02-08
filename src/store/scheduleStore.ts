import { create } from 'zustand';
import { addDays } from 'date-fns';
import type { 
  Class, 
  ScheduleAssignment, 
  ScheduleConstraints, 
  TeacherAvailability,
  ScheduleMetadata 
} from '../types';
import { analyzeScheduleComplexity, type SolverDecision } from '../lib/scheduleComplexity';
import { generateScheduleWithOrTools } from '../lib/apiClient';

interface ScheduleState {
  classes: Class[];
  teacherAvailability: TeacherAvailability[];
  assignments: ScheduleAssignment[];
  constraints: ScheduleConstraints;
  isGenerating: boolean;
  generationProgress: number;
  solverDecision: SolverDecision | null;
  schedulerVersion: 'stable' | 'dev';  // Updated to match Python backend versions
  lastGenerationMetadata: ScheduleMetadata | null;
  setClasses: (classes: Class[]) => void;
  setTeacherAvailability: (availability: TeacherAvailability[] | ((prev: TeacherAvailability[]) => TeacherAvailability[])) => void;
  setConstraints: (constraints: Partial<ScheduleConstraints>) => void;
  setSchedulerVersion: (version: 'stable' | 'dev') => void;  // Updated version type
  generateSchedule: () => Promise<void>;
  cancelGeneration: () => void;
}

// Test metadata for development
const testMetadata: ScheduleMetadata = {
  solver: 'cp-sat-dev',
  duration: 1250,
  score: 15750,
  distribution: {
    weekly: {
      variance: 0.75,
      classesPerWeek: {
        "0": 12,
        "1": 13,
        "2": 11,
        "3": 14
      },
      score: -75
    },
    daily: {
      byDate: {
        "2025-02-10": {
          periodSpread: 0.85,
          teacherLoadVariance: 0.5,
          classesByPeriod: {
            "1": 1,
            "2": 1,
            "3": 2,
            "4": 1,
            "5": 0,
            "6": 1,
            "7": 0,
            "8": 0
          }
        }
      },
      score: -425
    },
    totalScore: -500
  }
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

export const useScheduleStore = create<ScheduleState>((set, get) => {
  let worker: Worker | null = null;

  return {
    classes: [],
    teacherAvailability: [],
    assignments: [],
    constraints: defaultConstraints,
    isGenerating: false,
    generationProgress: 0,
    solverDecision: null,
    schedulerVersion: 'stable',
    lastGenerationMetadata: testMetadata,  // Use test metadata for development
    
    setClasses: (classes: Class[]) => set({ classes }),
    
    setTeacherAvailability: (availability: TeacherAvailability[] | ((prev: TeacherAvailability[]) => TeacherAvailability[])) => 
      set((state) => ({ 
        teacherAvailability: typeof availability === 'function' 
          ? availability(state.teacherAvailability)
          : availability 
      })),
    
    setConstraints: (newConstraints: Partial<ScheduleConstraints>) => 
      set((state) => ({
        constraints: { ...state.constraints, ...newConstraints }
      })),

    setSchedulerVersion: (version: 'stable' | 'dev') => set({ schedulerVersion: version }),
    
    generateSchedule: async () => {
      const { classes, teacherAvailability, constraints, schedulerVersion } = get();
      
      if (classes.length === 0) {
        throw new Error('No classes to schedule. Please add classes first.');
      }

      if (constraints.minPeriodsPerWeek > constraints.maxClassesPerWeek) {
        throw new Error('Minimum periods per week cannot be greater than maximum classes per week.');
      }

      // Analyze schedule complexity and choose solver
      const decision = analyzeScheduleComplexity(classes, teacherAvailability, constraints);
      set({ solverDecision: decision });

      set({ isGenerating: true, generationProgress: 0 });

      try {
        // Use Python backend solver via API
        const result = await generateScheduleWithOrTools(
          classes,
          teacherAvailability,
          constraints,
          schedulerVersion
        );

        set({
          assignments: result.assignments,
          lastGenerationMetadata: result.metadata,
          isGenerating: false,
          generationProgress: 100
        });
      } catch (error) {
        set({ isGenerating: false, generationProgress: 0 });
        throw error;
      }
    },

    cancelGeneration: () => {
      if (worker) {
        worker.terminate();
        worker = null;
        set({ isGenerating: false, generationProgress: 0 });
      }
    }
  };
});
