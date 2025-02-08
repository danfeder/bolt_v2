import { create } from 'zustand';
import { addDays } from 'date-fns';
import type { Class, ScheduleAssignment, ScheduleConstraints, TeacherAvailability } from '../types';
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
  lastGenerationMetadata: {
    solver: 'or-tools' | 'backtracking';
    duration: number;
    score: number;
  } | null;
  setClasses: (classes: Class[]) => void;
  setTeacherAvailability: (availability: TeacherAvailability[] | ((prev: TeacherAvailability[]) => TeacherAvailability[])) => void;
  setConstraints: (constraints: Partial<ScheduleConstraints>) => void;
  generateSchedule: () => Promise<void>;
  cancelGeneration: () => void;
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
    teacherAvailability: [],
    assignments: [],
    constraints: defaultConstraints,
    isGenerating: false,
    generationProgress: 0,
    solverDecision: null,
    lastGenerationMetadata: null,
    
    setClasses: (classes) => set({ classes }),
    
    setTeacherAvailability: (availability) => set((state) => ({ 
      teacherAvailability: typeof availability === 'function' 
        ? availability(state.teacherAvailability)
        : availability 
    })),
    
    setConstraints: (newConstraints) => set((state) => ({
      constraints: { ...state.constraints, ...newConstraints }
    })),
    
    generateSchedule: async () => {
      const { classes, teacherAvailability, constraints } = get();
      
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
        if (decision.solver === 'or-tools') {
          // Use OR-Tools solver via API
          const result = await generateScheduleWithOrTools(
            classes,
            teacherAvailability,
            constraints
          );

          set({
            assignments: result.assignments,
            lastGenerationMetadata: result.metadata,
            isGenerating: false,
            generationProgress: 100
          });
        } else {
          // Use local backtracking solver
          // Terminate existing worker if any
          if (worker) {
            worker.terminate();
          }

          // Create new worker
          worker = new Worker(
            new URL('../lib/schedulerWorker.ts', import.meta.url),
            { type: 'module' }
          );

          await new Promise<void>((resolve, reject) => {
            if (!worker) return reject(new Error('Worker failed to initialize'));

            worker.onmessage = (e) => {
              const { type, assignments, progress, error } = e.data;

              switch (type) {
                case 'progress':
                  set({ generationProgress: progress });
                  break;
                case 'success':
                  set({ 
                    assignments,
                    lastGenerationMetadata: {
                      solver: 'backtracking',
                      duration: Date.now() - startTime,
                      score: 0 // TODO: Implement scoring for backtracking algorithm
                    },
                    isGenerating: false,
                    generationProgress: 100
                  });
                  worker?.terminate();
                  worker = null;
                  resolve();
                  break;
                case 'error':
                  set({ isGenerating: false, generationProgress: 0 });
                  worker?.terminate();
                  worker = null;
                  reject(new Error(error));
                  break;
              }
            };

            worker.onerror = (error) => {
              set({ isGenerating: false, generationProgress: 0 });
              worker?.terminate();
              worker = null;
              reject(new Error('Worker error: ' + error.message));
            };

            const startTime = Date.now();

            // Start the worker
            worker.postMessage({
              classes,
              teacherAvailability,
              startDate: constraints.startDate,
              endDate: constraints.endDate,
              maxClassesPerDay: constraints.maxClassesPerDay,
              maxClassesPerWeek: constraints.maxClassesPerWeek,
              minPeriodsPerWeek: constraints.minPeriodsPerWeek,
              maxConsecutiveClasses: constraints.maxConsecutiveClasses,
              consecutiveClassesRule: constraints.consecutiveClassesRule
            });
          });
        }
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
