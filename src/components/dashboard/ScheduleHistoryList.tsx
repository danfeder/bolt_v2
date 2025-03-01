import React, { useEffect } from 'react';
import { useDashboardStore } from '../../store/dashboardStore';
import { format, parseISO } from 'date-fns';

/**
 * Component for displaying schedule history and selecting schedules for comparison
 */
export const ScheduleHistoryList: React.FC = () => {
  const { 
    scheduleHistory, 
    selectedScheduleId, 
    comparisonScheduleId,
    loadScheduleHistory,
    selectSchedule,
    selectComparisonSchedule,
    compareSchedules,
    isComparing
  } = useDashboardStore();
  
  // Load schedule history on mount
  useEffect(() => {
    loadScheduleHistory();
  }, [loadScheduleHistory]);
  
  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      return format(parseISO(timestamp), 'MMM d, yyyy h:mm a');
    } catch (e) {
      return timestamp;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 75) return 'text-green-500';
    if (score >= 65) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Sort history by timestamp (newest first)
  const sortedHistory = [...scheduleHistory].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  if (scheduleHistory.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-4 h-full">
        <h3 className="text-lg font-medium text-gray-800 mb-4">Schedule History</h3>
        <div className="flex flex-col items-center justify-center h-48 text-gray-500">
          <p>No schedule history available</p>
          <p className="text-sm mt-2">Generate schedules to view comparison data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-4 h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-800">Schedule History</h3>
        <button
          onClick={() => compareSchedules()}
          disabled={!selectedScheduleId || !comparisonScheduleId || isComparing}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors
            ${(!selectedScheduleId || !comparisonScheduleId || isComparing)
              ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
        >
          {isComparing ? 'Comparing...' : 'Compare Selected'}
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Schedule
              </th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Generated
              </th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Score
              </th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Select
              </th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Compare
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedHistory.map((schedule) => (
              <tr key={schedule.id}>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-800">
                  {schedule.id}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                  {formatTimestamp(schedule.timestamp)}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm">
                  <span className={`font-medium ${getScoreColor(schedule.metrics.overall_score)}`}>
                    {schedule.metrics.overall_score.toFixed(1)}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm">
                  <input
                    type="radio"
                    name="selectedSchedule"
                    checked={selectedScheduleId === schedule.id}
                    onChange={() => selectSchedule(schedule.id)}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm">
                  <input
                    type="radio"
                    name="comparisonSchedule"
                    checked={comparisonScheduleId === schedule.id}
                    onChange={() => selectComparisonSchedule(schedule.id)}
                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-3 text-xs text-gray-500">
        <p>Select two schedules to compare their metrics and performance</p>
      </div>
    </div>
  );
};
