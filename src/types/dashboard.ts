/**
 * Dashboard type definitions based on backend API models
 */

export interface ChartDataPoint {
  x: string | number;
  y: number;
  category?: string;
}

export interface ChartDataSeries {
  name: string;
  data: ChartDataPoint[];
  color?: string;
}

export interface ChartData {
  series: ChartDataSeries[];
  title: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  type: 'bar' | 'line' | 'pie' | 'heatmap';
}

export interface GradePeriodHeatmapCell {
  grade: string;
  period: number;
  value: number;
}

export interface ConstraintSatisfactionMetric {
  name: string;
  satisfied: number;
  total: number;
  percentage: number;
  category: string;
}

export interface ScheduleQualityMetrics {
  distribution_score: number;
  preference_satisfaction: number;
  workload_balance: number;
  period_spread: number;
  overall_score: number;
}

export interface ScheduleComparisonResult {
  metric_name: string;
  baseline_value: number;
  comparison_value: number;
  difference: number;
  percentage_change: number;
  improvement: boolean;
}

export interface DashboardData {
  schedule_id: string;
  timestamp: string;
  quality_metrics: ScheduleQualityMetrics;
  daily_distribution: ChartData;
  period_distribution: ChartData;
  grade_distribution: ChartData;
  constraint_satisfaction: ConstraintSatisfactionMetric[];
  grade_period_heatmap: GradePeriodHeatmapCell[];
}
