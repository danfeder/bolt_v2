export interface TimeSlot {
  dayOfWeek: number;  // 1-5 for Monday-Friday
  period: number;     // 1-8
}

export interface RequiredPeriod {
  date: string;
  period: number;
}

export interface ConflictPeriod {
  dayOfWeek: number;
  period: number;
}

export interface Class {
  name: string;
  grade: string;
  conflicts: ConflictPeriod[];
  required_periods: RequiredPeriod[];
}

export interface InstructorAvailability {
  date: string;
  periods: number[];  // List of periods when instructor is unavailable
}

export interface ScheduleConstraints {
  maxClassesPerDay: number;
  maxClassesPerWeek: number;
  minPeriodsPerWeek: number;
  maxConsecutiveClasses: 1 | 2;
  consecutiveClassesRule: 'hard' | 'soft';
  startDate: string;
  endDate: string;
}

export interface ScheduleAssignment {
  name: string;  // Class name (e.g., PK207)
  date: string;
  timeSlot: TimeSlot;
}

export interface GeneticParams {
  populationSize: number;
  eliteSize: number;
  mutationRate: number;
  crossoverRate: number;
  maxGenerations: number;
}

export interface GeneticSolverConfig extends GeneticParams {
  enabled: boolean;
}

export interface GeneticMetrics {
  generation: number;
  maxGenerations: number;
  bestFitness: number;
  populationDiversity: number;
  averageFitness: number;
}

export interface SolverDecision {
  solverType: 'genetic' | 'cpsat';
  reason: string;
  metrics: {
    totalClasses: number;
    totalDays: number;
    constraintComplexity: number;
    teacherConflicts: number;
    overallComplexity: number;
  };
}

export interface SolverConfig {
  weights: SolverWeights;
  genetic: GeneticSolverConfig;
}

export interface ScheduleMetadata {
  duration_ms: number;
  solutions_found: number;
  score: number;
  gap: number;
  distribution?: DistributionMetrics;
  genetic?: GeneticMetrics;
}

export interface WeeklyDistributionMetrics {
  variance: number;
  classesPerWeek: Record<string, number>;
  score: number;
}

export interface DailyDistributionMetrics {
  periodSpread: number;
  classLoadVariance: number;  // renamed from teacherLoadVariance
  classesByPeriod: Record<string, number>;
}

export interface DistributionMetrics {
  weekly: WeeklyDistributionMetrics;
  daily: Record<string, DailyDistributionMetrics>;
  totalScore: number;
}

export interface SolverWeights {
  final_week_compression: number;
  day_usage: number;
  daily_balance: number;
  preferred_periods: number;
  distribution: number;
  avoid_periods: number;
  earlier_dates: number;
}

// New interfaces for tabbed interface
export type SchedulerTab = 'setup' | 'visualize' | 'dashboard' | 'debug';

export interface TabState {
  currentTab: SchedulerTab;
  setupComplete: boolean;
  visualizationReady: boolean;
}

export interface TabValidationState {
  setup: boolean;
  visualize: boolean;
  dashboard: boolean;
  debug: boolean;
}
