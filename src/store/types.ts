import type { ScheduleAssignment, ScheduleMetadata } from '../types';

export interface ComparisonResult {
  stable: {
    assignments: ScheduleAssignment[];
    metadata: ScheduleMetadata;
  };
  dev: {
    assignments: ScheduleAssignment[];
    metadata: ScheduleMetadata;
  };
  differences: {
    total_differences: number;
    differences: Array<{
      type: 'missing_in_stable' | 'missing_in_dev' | 'different_assignment';
      classId: string;
      stable?: ScheduleAssignment;
      dev?: ScheduleAssignment;
    }>;
  };
  metrics: {
    score: number;
    duration: number;
    distribution: {
      score_difference: number;
      weekly_variance_difference: number;
      average_period_spread_difference: number;
    };
  };
}

export interface ScheduleComparisonProps {
  result: ComparisonResult | null;
  isComparing: boolean;
  onCompare: () => void;
}
