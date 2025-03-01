import React from 'react';
import type { ScheduleQualityMetrics } from '../../types/dashboard';

interface QualityMetricsCardProps {
  metrics: ScheduleQualityMetrics;
}

/**
 * Component for displaying schedule quality metrics
 */
export const QualityMetricsCard: React.FC<QualityMetricsCardProps> = ({ metrics }) => {
  // Calculate color based on score value
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-500';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 90) return 'bg-green-100';
    if (score >= 80) return 'bg-green-50';
    if (score >= 70) return 'bg-yellow-50';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-50';
  };

  // Format score to one decimal place
  const formatScore = (score: number) => score.toFixed(1);

  return (
    <div className="bg-white shadow rounded-lg p-4 h-full">
      <h3 className="text-lg font-medium text-gray-800 mb-4">Schedule Quality</h3>
      
      {/* Overall Score */}
      <div className={`${getScoreBgColor(metrics.overall_score)} rounded-lg p-4 mb-4 flex items-center justify-between`}>
        <span className="text-gray-700 font-medium">Overall Score</span>
        <span className={`text-2xl font-bold ${getScoreColor(metrics.overall_score)}`}>
          {formatScore(metrics.overall_score)}
        </span>
      </div>

      {/* Individual Metrics */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Distribution Score</span>
          <span className={`font-medium ${getScoreColor(metrics.distribution_score)}`}>
            {formatScore(metrics.distribution_score)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Preference Satisfaction</span>
          <span className={`font-medium ${getScoreColor(metrics.preference_satisfaction)}`}>
            {formatScore(metrics.preference_satisfaction)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Workload Balance</span>
          <span className={`font-medium ${getScoreColor(metrics.workload_balance)}`}>
            {formatScore(metrics.workload_balance)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Period Spread</span>
          <span className={`font-medium ${getScoreColor(metrics.period_spread)}`}>
            {formatScore(metrics.period_spread)}
          </span>
        </div>
      </div>

      {/* Interpretation */}
      <div className="mt-6 pt-4 border-t border-gray-100">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Interpretation</h4>
        <p className="text-sm text-gray-600">
          {metrics.overall_score >= 85 
            ? "Excellent schedule quality with balanced distribution and high preference satisfaction."
            : metrics.overall_score >= 75
              ? "Good schedule quality with reasonable balance and preference satisfaction."
              : metrics.overall_score >= 65
                ? "Average schedule quality. Consider adjusting constraints for better results."
                : "Below average schedule quality. Review constraints and class requirements."}
        </p>
      </div>
    </div>
  );
};
