import React from 'react';
import { useDashboardStore } from '../../store/dashboardStore';
import type { ScheduleComparisonResult } from '../../types/dashboard';

/**
 * Component for displaying schedule comparison results
 */
export const ScheduleComparison: React.FC = () => {
  const { 
    comparisonResults,
    selectedScheduleId,
    comparisonScheduleId,
    isComparing,
    error
  } = useDashboardStore();

  if (isComparing) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mr-3"></div>
        <span className="text-gray-600">Comparing schedules...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-300 rounded-md p-4">
        <div className="flex">
          <div className="text-red-500">
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error comparing schedules</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!comparisonResults || !selectedScheduleId || !comparisonScheduleId) {
    return (
      <div>
        <h3 className="text-lg font-medium text-gray-800 mb-4">Schedule Comparison</h3>
        <div className="bg-gray-50 border border-gray-200 rounded-md p-6 text-center">
          <p className="text-gray-500 mb-2">Select two schedules to compare</p>
          <p className="text-sm text-gray-400">
            Compare different scheduling algorithms or constraint settings to see their impact
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-800">Schedule Comparison</h3>
        <div className="text-sm text-gray-500">
          Comparing <span className="font-medium">{selectedScheduleId}</span> with <span className="font-medium">{comparisonScheduleId}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr className="bg-gray-50">
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metric</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Baseline</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comparison</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Difference</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Change</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {comparisonResults.map((result, index) => (
              <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {result.metric_name}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {result.baseline_value.toFixed(1)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {result.comparison_value.toFixed(1)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {result.difference > 0 ? '+' : ''}{result.difference.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm">
                  <ComparisonBadge result={result} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-4 bg-blue-50 border border-blue-100 rounded-md">
        <h4 className="text-sm font-medium text-blue-800 mb-2">Insights</h4>
        <p className="text-sm text-blue-700">
          {generateInsights(comparisonResults)}
        </p>
      </div>
    </div>
  );
};

// Helper component for rendering comparison badges
const ComparisonBadge: React.FC<{ result: ScheduleComparisonResult }> = ({ result }) => {
  const { percentage_change, improvement } = result;
  
  if (Math.abs(percentage_change) < 1) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        No change
      </span>
    );
  }
  
  if (improvement) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        +{percentage_change.toFixed(1)}%
      </span>
    );
  }
  
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
      {percentage_change.toFixed(1)}%
    </span>
  );
};

// Helper function to generate insights text
function generateInsights(results: ScheduleComparisonResult[]): string {
  const improvements = results.filter(r => r.improvement && r.percentage_change > 2);
  const regressions = results.filter(r => !r.improvement && r.percentage_change > 2);
  
  if (improvements.length === 0 && regressions.length === 0) {
    return "Both schedules perform similarly with no significant differences in metrics.";
  }
  
  let insights = '';
  
  if (improvements.length > 0) {
    const topImprovement = improvements.sort((a, b) => b.percentage_change - a.percentage_change)[0];
    insights += `The comparison schedule shows significant improvement in ${topImprovement.metric_name.toLowerCase()} (${topImprovement.percentage_change.toFixed(1)}% better). `;
    
    if (improvements.length > 1) {
      insights += `Also improved: ${improvements.slice(1, 3).map(i => i.metric_name.toLowerCase()).join(', ')}. `;
    }
  }
  
  if (regressions.length > 0) {
    const topRegression = regressions.sort((a, b) => b.percentage_change - a.percentage_change)[0];
    insights += `However, the comparison schedule performs worse in ${topRegression.metric_name.toLowerCase()} (${topRegression.percentage_change.toFixed(1)}% decrease). `;
  }
  
  return insights || "Comparison shows mixed results with minor differences between schedules.";
}
