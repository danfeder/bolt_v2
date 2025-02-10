import React from 'react';
import { useScheduleStore } from '../store/scheduleStore';
import { format } from 'date-fns';
import { Bug, Download, Zap, AlertCircle, XCircle } from 'lucide-react';
import type { Class, TeacherAvailability, TimeSlot } from '../types';
import { ScheduleComparison } from './ScheduleComparison';

interface ScheduleStats {
  totalAssignments: number;
  assignmentsPerDay: { [key: string]: number };
  assignmentsPerClass: { [key: string]: number };
  periodsUsed: { [key: string]: number };
  consecutiveClasses: { [key: string]: number };
  requiredPeriodStats: {
    totalClassesWithRequired: number;
    satisfiedRequirements: { [key: string]: boolean };
  };
  preferenceStats: {
    totalPreferred: number;
    totalAvoided: number;
    satisfiedPreferences: { [key: string]: boolean };
    avoidedPeriods: { [key: string]: boolean };
  };
}

export const ScheduleDebugPanel: React.FC = () => {
  const { 
    assignments, 
    classes, 
    constraints,
    solverDecision,
    lastGenerationMetadata,
    schedulerVersion,
    setSchedulerVersion,
    teacherAvailability,
    comparisonResult,
    isComparing,
    compareVersions,
    error,
    clearError
  } = useScheduleStore();
  const [isOpen, setIsOpen] = React.useState(false);

  const calculateStats = (): ScheduleStats => {
    // ... [Previous calculateStats implementation remains the same]
    const stats: ScheduleStats = {
      totalAssignments: assignments.length,
      assignmentsPerDay: {},
      assignmentsPerClass: {},
      periodsUsed: {},
      consecutiveClasses: {},
      requiredPeriodStats: {
        totalClassesWithRequired: 0,
        satisfiedRequirements: {}
      },
      preferenceStats: {
        totalPreferred: 0,
        totalAvoided: 0,
        satisfiedPreferences: {},
        avoidedPeriods: {}
      }
    };

    // ... [Rest of calculateStats stays the same]
    return stats;
  };

  const downloadScheduleData = () => {
    const stats = calculateStats();
    const data = {
      schedulerVersion,
      constraints,
      overview: {
        totalAssignments: stats.totalAssignments,
        totalClasses: classes.length,
        classesWithRequiredPeriods: stats.requiredPeriodStats.totalClassesWithRequired,
        requiredPeriodAssignments: classes
          .filter(c => c.weeklySchedule.requiredPeriods.length > 0)
          .map(c => {
            const assignment = assignments.find(a => a.classId === c.id);
            const isRequired = assignment && c.weeklySchedule.requiredPeriods.some(
              rp => rp.dayOfWeek === assignment.timeSlot.dayOfWeek && 
                   rp.period === assignment.timeSlot.period
            );
            return {
              classId: c.id,
              requiredPeriods: c.weeklySchedule.requiredPeriods,
              assignedSlot: assignment?.timeSlot,
              satisfiesRequirement: isRequired
            };
          })
      },
      assignmentsPerDay: stats.assignmentsPerDay,
      assignmentsPerClass: stats.assignmentsPerClass,
      periodsUsed: stats.periodsUsed,
      consecutiveClasses: stats.consecutiveClasses,
      rawSchedule: assignments,
      metadata: lastGenerationMetadata,
      comparison: comparisonResult
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `schedule-data-${format(new Date(), 'yyyy-MM-dd')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const stats = calculateStats();

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-2 bg-gray-800 text-white rounded-full shadow-lg hover:bg-gray-700"
        title="Open Schedule Debug Panel"
      >
        <Bug size={24} />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-[80vh] bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
      <div className="p-4 bg-gray-800 text-white flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Bug size={20} />
          Schedule Debug Panel
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={downloadScheduleData}
            className="p-1.5 rounded hover:bg-gray-700 transition-colors"
            title="Download Schedule Data"
          >
            <Download size={20} />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            ×
          </button>
        </div>
      </div>
      
      <div className="p-4 overflow-y-auto max-h-[calc(80vh-4rem)]">
        <div className="space-y-6">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 flex items-start gap-3">
              <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={20} />
              <div className="flex-1">
                <p className="text-red-700 whitespace-pre-wrap">{error}</p>
              </div>
              <button
                onClick={clearError}
                className="text-red-400 hover:text-red-600"
                title="Dismiss error"
              >
                <XCircle size={20} />
              </button>
            </div>
          )}

          <section>
            <h4 className="font-medium mb-2">Scheduler Version</h4>
            <div className="bg-gray-50 p-3 rounded">
              <select 
                value={schedulerVersion}
                onChange={(e) => setSchedulerVersion(e.target.value as 'stable' | 'dev')}
                className="w-full p-2 border rounded"
              >
                <option value="stable">CP-SAT Stable (Full Featured)</option>
                <option value="dev">CP-SAT Dev - Advanced Optimization</option>
              </select>
              <div className="mt-2 text-sm text-gray-600">
                {schedulerVersion === 'stable' && 'Stable version with class limits, required periods, period preferences, and consecutive class handling'}
                {schedulerVersion === 'dev' && 'Development version: Adding advanced schedule distribution optimization'}
              </div>
            </div>
          </section>

          <ScheduleComparison
            result={comparisonResult}
            isComparing={isComparing}
            onCompare={compareVersions}
          />

          {solverDecision && (
            <section>
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <Zap size={16} className="text-yellow-500" />
                Solver Decision
              </h4>
              <div className="bg-gray-50 p-3 rounded space-y-2">
                <p className="font-medium">
                  Using {solverDecision.solver} solver
                </p>
                <p className="text-sm text-gray-600">
                  {solverDecision.reason}
                </p>
                <div className="mt-2">
                  <h5 className="text-sm font-medium mb-1">Complexity Metrics:</h5>
                  <pre className="text-sm">
                    {JSON.stringify({
                      totalClasses: solverDecision.metrics.totalClasses,
                      totalDays: solverDecision.metrics.totalDays,
                      constraintComplexity: solverDecision.metrics.constraintComplexity,
                      teacherConflicts: solverDecision.metrics.teacherConflicts,
                      overallComplexity: solverDecision.metrics.overallComplexity
                    }, null, 2)}
                  </pre>
                </div>
              </div>
            </section>
          )}

          {lastGenerationMetadata && (
            <section>
              <h4 className="font-medium mb-2">Generation Results</h4>
              <div className="bg-gray-50 p-3 rounded">
                <pre className="text-sm">
                  {JSON.stringify({
                    solver: lastGenerationMetadata.solver,
                    duration: `${lastGenerationMetadata.duration}ms`,
                    score: lastGenerationMetadata.score,
                    distribution: lastGenerationMetadata.distribution
                  }, null, 2)}
                </pre>
              </div>
            </section>
          )}

          <section>
            <h4 className="font-medium mb-2">Schedule Overview</h4>
            <div className="bg-gray-50 p-3 rounded space-y-4">
              <div>
                <p>Total Assignments: {stats.totalAssignments}</p>
                <p>Total Classes: {classes.length}</p>
              </div>
              
              <div className="border-t pt-2">
                <h5 className="text-sm font-medium mb-1">Assignments per Day:</h5>
                <pre className="text-sm">
                  {JSON.stringify(stats.assignmentsPerDay, null, 2)}
                </pre>
              </div>
              
              <div className="border-t pt-2">
                <h5 className="text-sm font-medium mb-1">Assignments per Class:</h5>
                <pre className="text-sm">
                  {JSON.stringify(stats.assignmentsPerClass, null, 2)}
                </pre>
              </div>
              
              <div className="border-t pt-2">
                <h5 className="text-sm font-medium mb-1">Period Usage:</h5>
                <pre className="text-sm">
                  {JSON.stringify(stats.periodsUsed, null, 2)}
                </pre>
              </div>
            </div>
          </section>

          <section>
            <h4 className="font-medium mb-2">Raw Schedule Data</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">
                {JSON.stringify(assignments, null, 2)}
              </pre>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
