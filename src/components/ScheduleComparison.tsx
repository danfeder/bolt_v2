import React from 'react';
import { GitCompare } from 'lucide-react';
import type { ScheduleComparisonProps } from '../store/types';

export const ScheduleComparison: React.FC<ScheduleComparisonProps> = ({
  result,
  isComparing,
  onCompare
}) => {
  if (!result && !isComparing) {
    return (
      <div className="bg-gray-50 p-3 rounded">
        <div className="flex items-center justify-between">
          <h4 className="font-medium">Version Comparison</h4>
          <button
            onClick={onCompare}
            disabled={isComparing}
            className="flex items-center gap-1 px-2 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 disabled:opacity-50"
            title="Compare stable and dev versions"
          >
            <GitCompare size={16} />
            Compare Versions
          </button>
        </div>
      </div>
    );
  }

  if (isComparing) {
    return (
      <div className="bg-gray-50 p-3 rounded">
        <div className="flex items-center justify-between">
          <h4 className="font-medium">Version Comparison</h4>
          <div className="flex items-center gap-2 text-blue-600">
            <GitCompare size={16} className="animate-spin" />
            <span className="text-sm">Comparing...</span>
          </div>
        </div>
      </div>
    );
  }

  // At this point, result must be non-null because we've handled all other cases
  if (!result) return null;

  return (
    <section>
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium">Version Comparison</h4>
        <button
          onClick={onCompare}
          className="flex items-center gap-1 px-2 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
          title="Run comparison again"
        >
          <GitCompare size={16} />
          Compare Again
        </button>
      </div>

      <div className="bg-gray-50 p-3 rounded space-y-4">
        <div>
          <h5 className="text-sm font-medium mb-1">Schedule Differences:</h5>
          <div className="text-sm">
            Total differences: {result.differences.total_differences}
          </div>
          {result.differences.total_differences > 0 && (
            <div className="mt-2 space-y-2">
              {result.differences.differences.map((diff, index) => (
                <div 
                  key={index} 
                  className="border-l-4 pl-2"
                  style={{
                    borderColor: diff.type === 'missing_in_stable' ? '#dc2626' :
                               diff.type === 'missing_in_dev' ? '#f59e0b' : '#16a34a'
                  }}
                >
                  <div className="font-medium">Class {diff.classId}</div>
                  <div className="text-sm">
                    {diff.type === 'different_assignment' ? (
                      <>
                        Stable: Day {diff.stable?.timeSlot.dayOfWeek}, 
                        Period {diff.stable?.timeSlot.period}
                        <br />
                        Dev: Day {diff.dev?.timeSlot.dayOfWeek}, 
                        Period {diff.dev?.timeSlot.period}
                      </>
                    ) : (
                      `Missing in ${diff.type === 'missing_in_stable' ? 'stable' : 'dev'} version`
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h5 className="text-sm font-medium mb-1">Performance Comparison:</h5>
          <div className="space-y-1">
            <div className="text-sm">
              Score difference: {result.metrics.score > 0 ? '+' : ''}
              {result.metrics.score}
              {result.metrics.score !== 0 && (
                <span className="text-xs ml-1">
                  ({result.metrics.score > 0 ? 'dev better' : 'stable better'})
                </span>
              )}
            </div>
            <div className="text-sm">
              Duration difference: {result.metrics.duration}ms
              {result.metrics.duration !== 0 && (
                <span className="text-xs ml-1">
                  ({result.metrics.duration < 0 ? 'dev faster' : 'stable faster'})
                </span>
              )}
            </div>
          </div>
        </div>

        <div>
          <h5 className="text-sm font-medium mb-1">Distribution Improvements:</h5>
          <div className="space-y-1">
            <div className="text-sm">
              Weekly variance: {result.metrics.distribution.weekly_variance_difference > 0 ? '+' : ''}
              {result.metrics.distribution.weekly_variance_difference.toFixed(2)}
            </div>
            <div className="text-sm">
              Period spread: {result.metrics.distribution.average_period_spread_difference > 0 ? '+' : ''}
              {(result.metrics.distribution.average_period_spread_difference * 100).toFixed(1)}%
            </div>
            <div className="text-sm">
              Overall distribution: {result.metrics.distribution.score_difference > 0 ? '+' : ''}
              {result.metrics.distribution.score_difference.toFixed(0)}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
