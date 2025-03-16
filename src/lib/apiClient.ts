import type { 
  Class, 
  ScheduleAssignment, 
  ScheduleConstraints, 
  InstructorAvailability,
  ScheduleMetadata,
  // SolverWeights, // Commented out - unused
  GeneticSolverConfig,
  SolverConfig,
  ConstraintCategory,
  ConstraintMetadata
} from '../types';
import type {
  DashboardData,
  ChartData,
  ScheduleQualityMetrics,
  ScheduleComparisonResult
} from '../types/dashboard';
import type { ComparisonResult } from '../store/types';

export class ApiClient {
  private _csrfToken: string | null = null; // Prefixed with _ to indicate it's not currently being used
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

  /**
   * Get all constraint categories
   * @returns List of constraint categories with metadata
   */
  async getConstraintCategories(): Promise<ConstraintCategory[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/constraints/categories`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to get constraint categories');
      }

      return await response.json();
    } catch (error) {
      console.error('Constraint categories error:', error);
      throw error;
    }
  }

  /**
   * Get information about a specific constraint
   * @param constraintName The name of the constraint
   * @returns Constraint metadata
   */
  async getConstraintInfo(constraintName: string): Promise<ConstraintMetadata> {
    try {
      const response = await fetch(`${this.baseUrl}/api/constraints/${constraintName}`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Failed to get constraint info');
      }

      return await response.json();
    } catch (error) {
      console.error(`Constraint info error for ${constraintName}:`, error);
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
    startDate: string;  // Same as parent startDate
    endDate: string;    // Same as parent endDate
    allowConsecutiveClasses?: boolean; // Optional - defaults to true on backend
    requiredBreakPeriods?: number[];   // Optional - defaults to empty array on backend
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
      ? 'http://localhost:8000/api/v1/scheduler' // Updated development URL for scheduler
      : '/api/v1/scheduler'; // Updated production URL for scheduler
  } else {
    // We're in a Node.js environment (tests)
    return 'http://localhost:8000/api/v1/scheduler'; // Updated default URL for tests
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
    // The full path is /api/v1/scheduler/schedule/{version} based on the backend API structure
    const url = `${SCHEDULER_URL}/schedule/${version}`;
    
    // Log request data for debugging
    console.log('Sending request to scheduler API:', {
      url,
      constraints: request.constraints,
      classCount: request.classes.length,
      startDate: request.startDate,
      endDate: request.endDate
    });
    
    // Add a simple test to verify API connectivity
    try {
      const healthCheck = await fetch('http://localhost:8000/health');
      console.log('Health check status:', healthCheck.status, healthCheck.statusText);
    } catch (healthError) {
      console.warn('Health check failed, API server may not be running:', healthError);
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...request,
        // Include genetic config only if provided
        ...(geneticConfig ? { geneticConfig } : {})
      }),
    });
    
    // Log response status for debugging
    console.log('Scheduler API response status:', response.status, response.statusText);
    
    // Check for empty response first
    const responseText = await response.text();
    
    if (!responseText || responseText.trim() === '') {
      throw new Error('Empty response from server. The API may not be running or accessible.');
    }
    
    // Now parse the JSON
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (parseError) {
      console.error('Failed to parse API response:', responseText);
      throw new Error(`Invalid JSON response: ${parseError instanceof Error ? parseError.message : 'Unknown parsing error'}`);
    }

    if (!response.ok) {
      // Log the complete error response for debugging
      console.log('Server error response details:', data);
      
      // Handle validation errors
      if (response.status === 422) {
        // Handle new error format with errors array
        if (data?.errors && Array.isArray(data.errors)) {
          const errorDetails = data.errors
            .map((err: any) => `${err.field || ''}: ${err.message || JSON.stringify(err)}`)
            .join('\n');
          throw new Error(`Validation errors:\n${errorDetails}`);
        }
        // Handle FastAPI validation error format
        else if (data?.detail && Array.isArray(data.detail)) {
          const errorMessage = data.detail
            .map((err: any) => `${err.loc?.join('.') || ''}: ${err.msg || JSON.stringify(err)}`)
            .join('\n');
          throw new Error(`Request validation errors:\n${errorMessage}`);
        }
        // Handle legacy validation error format
        else {
          const validationError = data;
          if (Array.isArray(validationError)) {
            const errorMessage = validationError
              .map((err: any) => err.msg || err.message || JSON.stringify(err))
              .join('\n');
            throw new Error(`Validation errors:\n${errorMessage}`);
          } else if (validationError.detail) {
            throw new Error(validationError.detail);
          }
        }
      }
      
      // Handle other API errors
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
    // Enhanced error logging with more context
    console.error('Schedule generation error:', { 
      message: error instanceof Error ? error.message : 'Unknown error',
      requestData: {
        startDate: request.startDate,
        endDate: request.endDate,
        maxClassesPerDay: request.constraints.maxClassesPerDay,
        maxClassesPerWeek: request.constraints.maxClassesPerWeek,
        classCount: request.classes.length
      },
      error
    });
    
    // Provide more user-friendly error message
    if (error instanceof Error) {
      if (error.message.includes('Unexpected end of JSON input')) {
        throw new Error('Unable to connect to the scheduling service. Please ensure the API server is running.');
      }
      throw error;
    }
    throw new Error('Failed to generate schedule. Check the browser console for more details.');
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
