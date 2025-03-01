import React, { useEffect } from 'react';
import { useDashboardStore } from '../../store/dashboardStore';
import { useScheduleStore } from '../../store/scheduleStore';
import { QualityMetricsCard } from './QualityMetricsCard';
import { DistributionChart } from './DistributionChart';
import { ConstraintSatisfactionCard } from './ConstraintSatisfactionCard';
import { GradePeriodHeatmap } from './GradePeriodHeatmap';
import { ScheduleHistoryList } from './ScheduleHistoryList';
import { ScheduleComparison } from './ScheduleComparison';

/**
 * Dashboard component for displaying schedule analysis and metrics
 */
export const Dashboard: React.FC = () => {
  const { 
    currentDashboard, 
    isLoading, 
    error,
    analyzeDashboard,
    loadScheduleHistory
  } = useDashboardStore();
  
  const { 
    classes, 
    instructorAvailability, 
    constraints, 
    schedulerVersion,
    assignments,
    tabValidation,
    markTabComplete
  } = useScheduleStore();

  // Load schedule history on mount
  useEffect(() => {
    loadScheduleHistory();
  }, [loadScheduleHistory]);
  
  // Analyze schedule if assignments exist but no dashboard data
  useEffect(() => {
    if (assignments.length > 0 && !currentDashboard && !isLoading) {
      analyzeDashboard(classes, instructorAvailability, constraints, schedulerVersion);
    }
  }, [
    assignments, 
    currentDashboard, 
    isLoading, 
    analyzeDashboard, 
    classes, 
    instructorAvailability, 
    constraints, 
    schedulerVersion
  ]);
  
  // Mark dashboard tab as complete when we have data
  useEffect(() => {
    if (currentDashboard && !tabValidation.dashboard) {
      markTabComplete('dashboard');
    }
  }, [currentDashboard, tabValidation.dashboard, markTabComplete]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-4 text-lg text-gray-600">Loading dashboard data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  if (!currentDashboard) {
    return (
      <div className="bg-yellow-50 border border-yellow-300 text-yellow-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">No Dashboard Data:</strong>
        <span className="block sm:inline"> Generate a schedule to view dashboard analysis</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold text-gray-800">
          Schedule Analysis Dashboard
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={() => analyzeDashboard(classes, instructorAvailability, constraints, schedulerVersion)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors"
          >
            Refresh Analysis
          </button>
        </div>
      </div>

      {/* Main Dashboard Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quality Metrics Card */}
        <div className="lg:col-span-1">
          <QualityMetricsCard metrics={currentDashboard.quality_metrics} />
        </div>

        {/* Schedule History */}
        <div className="lg:col-span-2">
          <ScheduleHistoryList />
        </div>
      </div>

      {/* Distribution Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg p-4">
          <DistributionChart 
            chartData={currentDashboard.daily_distribution} 
            title="Classes Per Day"
          />
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <DistributionChart 
            chartData={currentDashboard.period_distribution} 
            title="Classes Per Period"
          />
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <DistributionChart 
            chartData={currentDashboard.grade_distribution} 
            title="Classes Per Grade"
          />
        </div>
      </div>

      {/* Additional Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-4">
          <ConstraintSatisfactionCard 
            constraints={currentDashboard.constraint_satisfaction} 
          />
        </div>
        <div className="bg-white shadow rounded-lg p-4">
          <GradePeriodHeatmap 
            data={currentDashboard.grade_period_heatmap} 
          />
        </div>
      </div>

      {/* Schedule Comparison */}
      <div className="bg-white shadow rounded-lg p-4">
        <ScheduleComparison />
      </div>
    </div>
  );
};
