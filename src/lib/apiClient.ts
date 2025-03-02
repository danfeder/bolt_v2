import type { 
  Class, 
  ScheduleAssignment, 
  ScheduleConstraints, 
  InstructorAvailability,
  ScheduleMetadata,
  SolverWeights,
  GeneticSolverConfig,
  SolverConfig
} from '../types';
import type {
  DashboardData,
  ChartData,
  ScheduleQualityMetrics,
  ScheduleComparisonResult
} from '../types/dashboard';
import type { ComparisonResult } from '../store/types';

export class ApiClient {
  private csrfToken: string | null = null;
  private baseUrl: string;
  
  constructor() {
    // For tests, use a simplified approach without import.meta
    // This works in both browser and test environments
    
    // Check if we're in a browser environment with window
    if (typeof window !== 'undefined') {
      this.baseUrl = window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' // Development URL 
        : '/api'; // Production URL
    } else {
      // We're in a Node.js environment (tests)
      this.baseUrl = 'http://localhost:8000'; // Default to dev URL for tests
    }
  }

  async generateSchedule(
    classes: Class[],
    instructorAvailability: InstructorAvailability[],
    constraints: ScheduleConstraints,
    version: SchedulerVersion = 'stable',
    geneticConfig?: GeneticSolverConfig
  ): Promise<{ assignments: ScheduleAssignment[]; metadata: ScheduleResponse['metadata'] }> {
    return generateScheduleWithOrTools(classes, instructorAvailability, constraints, version, geneticConfig);
  }

  async compareSchedules(
    classes: Class[],
    instructorAvailability: InstructorAvailability[],
    constraints: ScheduleConstraints
  ): Promise<ComparisonResult> {
    return compareScheduleSolvers(classes, instructorAvailability, constraints);
  }

  async updateSolverConfig(config: SolverConfig): Promise<{ current: SolverConfig }> {
    const response = await fetch(`${this.baseUrl}/solver/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || data.message || 'Failed to update solver configuration');
    }
    
    const result = await response.json();
    return result;
  }

  async resetSolverConfig(): Promise<{ current: SolverConfig }> {
    const response = await fetch(`${this.baseUrl}/solver/config/reset`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || data.message || 'Failed to reset solver configuration');
    }
    
    const result = await response.json();
    return result;
  }

  /**
   * Analyze schedule and get dashboard data
   * @param classes Classes to schedule
   * @param instructorAvailability Teacher availability
   * @param constraints Scheduling constraints
   * @param solverType Solver type to use
   */
  async analyzeDashboard(
    classes: Class[],
    instructorAvailability: InstructorAvailability[],
    constraints: ScheduleConstraints,
    solverType: 'stable' | 'dev' = 'stable'
  ): Promise<DashboardData> {
    // Create request body
    const request: ScheduleRequest = {
      classes,
      instructorAvailability,
      startDate: constraints.startDate,
      endDate: constraints.endDate,
      constraints: {
        maxClassesPerDay: constraints.maxClassesPerDay,
        maxClassesPerWeek: constraints.maxClassesPerWeek,
        minPeriodsPerWeek: constraints.minPeriodsPerWeek,
        maxConsecutiveClasses: constraints.maxConsecutiveClasses,
        consecutiveClassesRule: constraints.consecutiveClassesRule,
        startDate: constraints.startDate,
        endDate: constraints.endDate
      },
    };

    try {
      const response = await fetch(`${this.baseUrl}/dashboard/analyze?solver_type=${solverType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to analyze schedule');
      }

      return await response.json();
    } catch (error) {
      console.error('Dashboard analysis error:', error);
      throw error;
    }
  }

  /**
   * Compare two schedules
   * @param baselineId Baseline schedule ID
   * @param comparisonId Comparison schedule ID
   */
  async compareSchedulesDashboard(
    baselineId: string,
    comparisonId: string
  ): Promise<ScheduleComparisonResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/dashboard/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          baseline_id: baselineId,
          comparison_id: comparisonId
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to compare schedules');
      }

      return await response.json();
    } catch (error) {
      console.error('Schedule comparison error:', error);
      throw error;
    }
  }

  /**
   * Get schedule history
   */
  async getScheduleHistory(): Promise<{ id: string; timestamp: string; metrics: ScheduleQualityMetrics }[]> {
    try {
      const response = await fetch(`${this.baseUrl}/dashboard/history`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to get schedule history');
      }

      return await response.json();
    } catch (error) {
      console.error('Schedule history error:', error);
      throw error;
    }
  }

  /**
   * Get schedule metrics
   * @param scheduleId Schedule ID
   */
  async getScheduleMetrics(scheduleId: string): Promise<ScheduleQualityMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/dashboard/metrics/${scheduleId}`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to get schedule metrics');
      }

      return await response.json();
    } catch (error) {
      console.error('Schedule metrics error:', error);
      throw error;
    }
  }

  /**
   * Get chart data
   * @param chartType Chart type
   * @param scheduleId Schedule ID
   */
  async getChartData(chartType: 'daily' | 'period' | 'grade', scheduleId: string): Promise<ChartData> {
    try {
      const response = await fetch(`${this.baseUrl}/dashboard/chart/${chartType}/${scheduleId}`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to get chart data');
      }

      return await response.json();
    } catch (error) {
      console.error('Chart data error:', error);
      throw error;
    }
  }
}

export const apiClient = new ApiClient();

interface ScheduleRequest {
  classes: Class[];
  instructorAvailability: InstructorAvailability[];
  startDate: string;
  endDate: string;
  constraints: {
    maxClassesPerDay: number;
    maxClassesPerWeek: number;
    minPeriodsPerWeek: number;
    maxConsecutiveClasses: 1 | 2;
    consecutiveClassesRule: 'hard' | 'soft';
    startDate: string;  // Added to match backend expectations
    endDate: string;    // Added to match backend expectations
  };
}

interface ScheduleResponse {
  assignments: ScheduleAssignment[];
  metadata: ScheduleMetadata;
}

interface ValidationError {
  detail: string;
  errors: Array<{
    location: string;
    message: string;
    type: string;
  }>;
}

const SCHEDULER_URL = (() => {
  // Check if we're in a browser environment with window
  if (typeof window !== 'undefined') {
    return window.location.hostname === 'localhost'
      ? 'http://localhost:8001' // Development URL for scheduler
      : '/scheduler'; // Production URL for scheduler
  } else {
    // We're in a Node.js environment (tests)
    return 'http://localhost:8001'; // Default to dev URL for tests
  }
})();

type SchedulerVersion = 'stable' | 'dev';

export async function generateScheduleWithOrTools(
  classes: Class[],
  instructorAvailability: InstructorAvailability[],
  constraints: ScheduleConstraints,
  version: SchedulerVersion = 'stable',
  geneticConfig?: GeneticSolverConfig
): Promise<{ assignments: ScheduleAssignment[]; metadata: ScheduleResponse['metadata'] }> {
  const request: ScheduleRequest = {
    classes,
    instructorAvailability,
    startDate: constraints.startDate,
    endDate: constraints.endDate,
    constraints: {
      maxClassesPerDay: constraints.maxClassesPerDay,
      maxClassesPerWeek: constraints.maxClassesPerWeek,
      minPeriodsPerWeek: constraints.minPeriodsPerWeek,
      maxConsecutiveClasses: constraints.maxConsecutiveClasses,
      consecutiveClassesRule: constraints.consecutiveClassesRule,
      startDate: constraints.startDate,
      endDate: constraints.endDate
    },
  };

  try {
    // Use explicit endpoint paths instead of query parameters
    const url = `${SCHEDULER_URL}/schedule/${version}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
      ...request,
      geneticConfig
    }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle validation errors
      if (response.status === 422) {
        const validationError = data;
        if (Array.isArray(validationError)) {
          const errorMessage = validationError
            .map(err => err.msg || err.message || JSON.stringify(err))
            .join('\n');
          throw new Error(`Validation errors:\n${errorMessage}`);
        } else if (validationError.detail) {
          throw new Error(validationError.detail);
        }
      }
      throw new Error(data.detail || data.message || 'Failed to generate schedule');
    }

    // Ensure we have a valid response structure
    if (!data.assignments || !data.metadata) {
      throw new Error('Invalid response format from server');
    }

    return {
      assignments: data.assignments,
      metadata: data.metadata,
    };
  } catch (error) {
    console.error('Schedule generation error:', error);
    throw error;
  }
}

export async function compareScheduleSolvers(
  classes: Class[],
  instructorAvailability: InstructorAvailability[],
  constraints: ScheduleConstraints
): Promise<ComparisonResult> {
  const request: ScheduleRequest = {
    classes,
    instructorAvailability,
    startDate: constraints.startDate,
    endDate: constraints.endDate,
    constraints: {
      maxClassesPerDay: constraints.maxClassesPerDay,
      maxClassesPerWeek: constraints.maxClassesPerWeek,
      minPeriodsPerWeek: constraints.minPeriodsPerWeek,
      maxConsecutiveClasses: constraints.maxConsecutiveClasses,
      consecutiveClassesRule: constraints.consecutiveClassesRule,
      startDate: constraints.startDate,
      endDate: constraints.endDate
    },
  };

  try {
    const url = `${SCHEDULER_URL}/schedule/compare`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 422 && 'errors' in data) {
        const validationError = data as ValidationError;
        const errorMessage = validationError.errors
          .map(err => `${err.location}: ${err.message}`)
          .join('\n');
        throw new Error(`Validation error:\n${errorMessage}`);
      }
      throw new Error(data.detail || data.message || 'Failed to compare schedules');
    }
    
    // Transform API response to match ComparisonResult type
    return {
      stable: data.stable,
      dev: data.dev,
      differences: data.comparison.assignment_differences,
      metrics: data.comparison.metric_differences
    };
  } catch (error) {
    console.error('Schedule comparison error:', error);
    throw error;
  }
}
