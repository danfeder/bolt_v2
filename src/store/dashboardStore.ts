import { create } from 'zustand';
import { apiClient } from '../lib/apiClient';
import type { 
  Class, 
  InstructorAvailability, 
  ScheduleConstraints
} from '../types';
import type {
  DashboardData,
  ScheduleQualityMetrics,
  ScheduleComparisonResult
} from '../types/dashboard';

interface DashboardState {
  // Dashboard data
  currentDashboard: DashboardData | null;
  scheduleHistory: Array<{
    id: string;
    timestamp: string;
    metrics: ScheduleQualityMetrics;
  }>;
  selectedScheduleId: string | null;
  comparisonScheduleId: string | null;
  comparisonResults: ScheduleComparisonResult[] | null;
  
  // Loading states
  isLoading: boolean;
  isComparing: boolean;
  error: string | null;
  
  // Actions
  analyzeDashboard: (
    classes: Class[],
    instructorAvailability: InstructorAvailability[],
    constraints: ScheduleConstraints,
    solverType?: 'stable' | 'dev'
  ) => Promise<void>;
  loadScheduleHistory: () => Promise<void>;
  selectSchedule: (scheduleId: string) => void;
  selectComparisonSchedule: (scheduleId: string) => void;
  compareSchedules: () => Promise<void>;
  clearError: () => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Initial state
  currentDashboard: null,
  scheduleHistory: [],
  selectedScheduleId: null,
  comparisonScheduleId: null,
  comparisonResults: null,
  isLoading: false,
  isComparing: false,
  error: null,
  
  // Actions
  analyzeDashboard: async (
    classes: Class[],
    instructorAvailability: InstructorAvailability[],
    constraints: ScheduleConstraints,
    solverType: 'stable' | 'dev' = 'stable'
  ) => {
    try {
      set({ isLoading: true, error: null });
      
      const dashboardData = await apiClient.analyzeDashboard(
        classes,
        instructorAvailability,
        constraints,
        solverType
      );
      
      set({ 
        currentDashboard: dashboardData,
        selectedScheduleId: dashboardData.schedule_id,
        isLoading: false 
      });
      
      // Refresh schedule history after analysis
      get().loadScheduleHistory();
      
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to analyze schedule' 
      });
    }
  },
  
  loadScheduleHistory: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const history = await apiClient.getScheduleHistory();
      
      set({ 
        scheduleHistory: history,
        isLoading: false 
      });
      
    } catch (error) {
      set({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Failed to load schedule history' 
      });
    }
  },
  
  selectSchedule: (scheduleId: string) => {
    set({ selectedScheduleId: scheduleId });
  },
  
  selectComparisonSchedule: (scheduleId: string) => {
    set({ comparisonScheduleId: scheduleId });
  },
  
  compareSchedules: async () => {
    const { selectedScheduleId, comparisonScheduleId } = get();
    
    if (!selectedScheduleId || !comparisonScheduleId) {
      set({ error: 'Please select schedules to compare' });
      return;
    }
    
    try {
      set({ isComparing: true, error: null });
      
      const results = await apiClient.compareSchedulesDashboard(
        selectedScheduleId,
        comparisonScheduleId
      );
      
      set({ 
        comparisonResults: results,
        isComparing: false 
      });
      
    } catch (error) {
      set({ 
        isComparing: false, 
        error: error instanceof Error ? error.message : 'Failed to compare schedules' 
      });
    }
  },
  
  clearError: () => set({ error: null })
}));
