import React from 'react';
import { useScheduleStore } from '../store/scheduleStore';
import { format } from 'date-fns';
import { Bug, Download, Zap } from 'lucide-react';

interface ScheduleStats {
  totalAssignments: number;
  assignmentsPerDay: { [key: string]: number };
  assignmentsPerClass: { [key: string]: number };
  periodsUsed: { [key: string]: number };
  consecutiveClasses: { [key: string]: number };
}

export const ScheduleDebugPanel: React.FC = () => {
  const { 
    assignments, 
    classes, 
    constraints,
    solverDecision,
    lastGenerationMetadata
  } = useScheduleStore();
  const [isOpen, setIsOpen] = React.useState(false);

  const calculateStats = (): ScheduleStats => {
    const stats: ScheduleStats = {
      totalAssignments: assignments.length,
      assignmentsPerDay: {},
      assignmentsPerClass: {},
      periodsUsed: {},
      consecutiveClasses: {}
    };

    assignments.forEach(assignment => {
      const date = format(new Date(assignment.date), 'yyyy-MM-dd');
      const period = assignment.timeSlot.period;
      
      // Count assignments per day
      stats.assignmentsPerDay[date] = (stats.assignmentsPerDay[date] || 0) + 1;
      
      // Count assignments per class
      stats.assignmentsPerClass[assignment.classId] = 
        (stats.assignmentsPerClass[assignment.classId] || 0) + 1;
      
      // Count usage of each period
      stats.periodsUsed[period] = (stats.periodsUsed[period] || 0) + 1;
      
      // Count consecutive classes
      const key = `${date}-${period}`;
      const prevKey = `${date}-${period - 1}`;
      const nextKey = `${date}-${period + 1}`;
      
      if (stats.consecutiveClasses[prevKey] || stats.consecutiveClasses[nextKey]) {
        stats.consecutiveClasses[key] = 
          (stats.consecutiveClasses[key] || 1) + 1;
      } else {
        stats.consecutiveClasses[key] = 1;
      }
    });

    return stats;
  };

  const downloadScheduleData = () => {
    const stats = calculateStats();
    const data = {
      constraints: {
        startDate: constraints.startDate,
        endDate: constraints.endDate,
        maxClassesPerDay: constraints.maxClassesPerDay,
        maxClassesPerWeek: constraints.maxClassesPerWeek,
        maxConsecutiveClasses: constraints.maxConsecutiveClasses,
        consecutiveClassesRule: constraints.consecutiveClassesRule
      },
      overview: {
        totalAssignments: stats.totalAssignments,
        totalClasses: classes.length
      },
      assignmentsPerDay: stats.assignmentsPerDay,
      assignmentsPerClass: stats.assignmentsPerClass,
      periodsUsed: stats.periodsUsed,
      consecutiveClasses: stats.consecutiveClasses,
      rawSchedule: assignments
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
                    score: lastGenerationMetadata.score
                  }, null, 2)}
                </pre>
              </div>
            </section>
          )}

          <section>
            <h4 className="font-medium mb-2">Constraints</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">
                {JSON.stringify({
                  startDate: constraints.startDate,
                  endDate: constraints.endDate,
                  maxClassesPerDay: constraints.maxClassesPerDay,
                  maxClassesPerWeek: constraints.maxClassesPerWeek,
                  maxConsecutiveClasses: constraints.maxConsecutiveClasses,
                  consecutiveClassesRule: constraints.consecutiveClassesRule
                }, null, 2)}
              </pre>
            </div>
          </section>

          <section>
            <h4 className="font-medium mb-2">Overview</h4>
            <div className="bg-gray-50 p-3 rounded">
              <p>Total Assignments: {stats.totalAssignments}</p>
              <p>Total Classes: {classes.length}</p>
            </div>
          </section>

          <section>
            <h4 className="font-medium mb-2">Assignments Per Day</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">
                {JSON.stringify(stats.assignmentsPerDay, null, 2)}
              </pre>
            </div>
          </section>

          <section>
            <h4 className="font-medium mb-2">Assignments Per Class</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">
                {JSON.stringify(stats.assignmentsPerClass, null, 2)}
              </pre>
            </div>
          </section>

          <section>
            <h4 className="font-medium mb-2">Period Usage</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">
                {JSON.stringify(stats.periodsUsed, null, 2)}
              </pre>
            </div>
          </section>

          <section>
            <h4 className="font-medium mb-2">Consecutive Classes</h4>
            <div className="bg-gray-50 p-3 rounded">
              <pre className="text-sm">
                {JSON.stringify(stats.consecutiveClasses, null, 2)}
              </pre>
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
