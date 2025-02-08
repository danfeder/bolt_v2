import React from 'react';
import { useScheduleStore } from '../store/scheduleStore';
import { format } from 'date-fns';
import { Bug, Download, Zap } from 'lucide-react';
import { Class, TeacherAvailability, TimeSlot } from '../types';

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
    teacherAvailability
  } = useScheduleStore();
  const [isOpen, setIsOpen] = React.useState(false);

  const calculateStats = (): ScheduleStats => {
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

    // Count classes with required periods
    classes.forEach(classObj => {
      if (classObj.weeklySchedule.requiredPeriods.length > 0) {
        stats.requiredPeriodStats.totalClassesWithRequired++;
      }
      if (classObj.weeklySchedule.preferredPeriods.length > 0) {
        stats.preferenceStats.totalPreferred++;
      }
      if (classObj.weeklySchedule.avoidPeriods.length > 0) {
        stats.preferenceStats.totalAvoided++;
      }
    });

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
      schedulerVersion,
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
            <>
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

              {lastGenerationMetadata.distribution && (
                <section>
                  <h4 className="font-medium mb-2">Distribution Metrics</h4>
                  <div className="bg-gray-50 p-3 rounded space-y-4">
                    <div>
                      <h5 className="text-sm font-medium mb-2">Weekly Distribution</h5>
                      <div className="space-y-2">
                        <div>
                          <span className="text-sm text-gray-600">Variance:</span>
                          <span className="ml-2 font-medium">
                            {lastGenerationMetadata.distribution.weekly.variance.toFixed(2)}
                          </span>
                        </div>
                        <div>
                          <span className="text-sm text-gray-600">Classes per Week:</span>
                          <pre className="text-sm mt-1">
                            {JSON.stringify(lastGenerationMetadata.distribution.weekly.classesPerWeek, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h5 className="text-sm font-medium mb-2">Daily Distribution</h5>
                      <div className="space-y-2">
                        {Object.entries(lastGenerationMetadata.distribution.daily.byDate).map(([date, metrics]) => (
                          <div key={date} className="border-l-4 pl-2" style={{
                            borderColor: metrics.periodSpread >= 0.8 ? '#16a34a' : 
                                       metrics.periodSpread >= 0.6 ? '#f59e0b' : '#dc2626'
                          }}>
                            <div className="font-medium">{date}</div>
                            <div className="text-sm space-y-1">
                              <div>
                                Period Spread: {(metrics.periodSpread * 100).toFixed(1)}%
                              </div>
                              <div>
                                Teacher Load Variance: {metrics.teacherLoadVariance.toFixed(2)}
                              </div>
                              <div className="text-xs text-gray-600">
                                Classes by Period:
                                <pre className="mt-1">
                                  {JSON.stringify(metrics.classesByPeriod, null, 2)}
                                </pre>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h5 className="text-sm font-medium mb-2">Overall Distribution Score</h5>
                      <div className="text-lg font-medium">
                        {lastGenerationMetadata.distribution.totalScore.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Higher scores indicate better distribution
                      </div>
                    </div>
                  </div>
                </section>
              )}
            </>
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
            <div className="bg-gray-50 p-3 rounded space-y-2">
              <div>
                <p>Total Assignments: {stats.totalAssignments}</p>
                <p>Total Classes: {classes.length}</p>
              </div>

              <div className="border-t pt-2">
                <h5 className="text-sm font-medium mb-1">Period Preferences:</h5>
                <p>Classes with Preferred Periods: {stats.preferenceStats.totalPreferred}</p>
                <p>Classes with Avoid Periods: {stats.preferenceStats.totalAvoided}</p>
                {(stats.preferenceStats.totalPreferred > 0 || stats.preferenceStats.totalAvoided > 0) && (
                  <div className="mt-2">
                    <ul className="text-sm space-y-2">
                      {classes
                        .filter(c => 
                          c.weeklySchedule.preferredPeriods.length > 0 || 
                          c.weeklySchedule.avoidPeriods.length > 0
                        )
                        .map(c => {
                          const assignment = assignments.find(a => a.classId === c.id);
                          const isPreferred = assignment && c.weeklySchedule.preferredPeriods.some(
                            pp => pp.dayOfWeek === assignment.timeSlot.dayOfWeek && 
                                 pp.period === assignment.timeSlot.period
                          );
                          const isAvoided = assignment && c.weeklySchedule.avoidPeriods.some(
                            ap => ap.dayOfWeek === assignment.timeSlot.dayOfWeek && 
                                 ap.period === assignment.timeSlot.period
                          );
                          
                          return (
                            <li key={c.id} className="border-l-4 pl-2" style={{
                              borderColor: isPreferred ? '#16a34a' : 
                                         isAvoided ? '#dc2626' : '#f59e0b'
                            }}>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{c.id}:</span>
                                {isPreferred && 
                                  <span className="text-green-600">
                                    ✓ Scheduled in preferred period (weight: {c.weeklySchedule.preferenceWeight})
                                  </span>
                                }
                                {isAvoided && 
                                  <span className="text-red-600">
                                    ⚠ Scheduled in avoided period (weight: {c.weeklySchedule.avoidanceWeight})
                                  </span>
                                }
                                {!isPreferred && !isAvoided && 
                                  <span className="text-amber-600">
                                    ⚠ Not in preferred/avoided period
                                  </span>
                                }
                              </div>
                              {assignment && (
                                <div className="text-sm text-gray-600 mt-1">
                                  {c.weeklySchedule.preferredPeriods.length > 0 && (
                                    <div>Preferred: {c.weeklySchedule.preferredPeriods.map(
                                      pp => `Day ${pp.dayOfWeek}, Period ${pp.period}`
                                    ).join(' or ')}</div>
                                  )}
                                  {c.weeklySchedule.avoidPeriods.length > 0 && (
                                    <div>Avoid: {c.weeklySchedule.avoidPeriods.map(
                                      ap => `Day ${ap.dayOfWeek}, Period ${ap.period}`
                                    ).join(' or ')}</div>
                                  )}
                                  <div>
                                    Assigned: Day {assignment.timeSlot.dayOfWeek}, 
                                    Period {assignment.timeSlot.period}
                                  </div>
                                </div>
                              )}
                            </li>
                          );
                        })}
                    </ul>
                  </div>
                )}
              </div>
              <div>
                <p>Total Assignments: {stats.totalAssignments}</p>
                <p>Total Classes: {classes.length}</p>
              </div>
              <div className="border-t pt-2">
                <p>Classes with Required Periods: {stats.requiredPeriodStats.totalClassesWithRequired}</p>
                {stats.requiredPeriodStats.totalClassesWithRequired > 0 && (
                  <div className="mt-2">
                    <h5 className="text-sm font-medium">Required Period Classes:</h5>
                    <ul className="text-sm mt-1 space-y-2">
                      {classes
                        .filter(c => c.weeklySchedule.requiredPeriods.length > 0)
                        .map(c => {
                          const assignment = assignments.find(a => a.classId === c.id);
                          const isRequired = assignment && c.weeklySchedule.requiredPeriods.some(
                            rp => rp.dayOfWeek === assignment.timeSlot.dayOfWeek && 
                                 rp.period === assignment.timeSlot.period
                          );
                          
                          // Check for teacher conflicts
                          const teacherConflict = assignment && teacherAvailability.some(
                            (ta: TeacherAvailability) => {
                              const dateStr = new Date(assignment.date).toISOString().split('T')[0];
                              return ta.date === dateStr && ta.unavailableSlots.some(
                                (us: TimeSlot) => us.dayOfWeek === assignment.timeSlot.dayOfWeek && 
                                                us.period === assignment.timeSlot.period
                              );
                            }
                          );
                          
                          return (
                            <li key={c.id} className="border-l-4 pl-2" style={{
                              borderColor: isRequired ? '#16a34a' : 
                                         teacherConflict ? '#dc2626' : '#f59e0b'
                            }}>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{c.id}:</span>
                                {isRequired ? 
                                  <span className="text-green-600">✓ Scheduled in required period</span> :
                                  <span className="text-amber-600">⚠ Not in required period</span>
                                }
                              </div>
                              <div className="text-sm text-gray-600 mt-1">
                                <div>Required: {c.weeklySchedule.requiredPeriods.map(
                                  rp => `Day ${rp.dayOfWeek}, Period ${rp.period}`
                                ).join(' or ')}</div>
                                {assignment && (
                                  <div>
                                    Assigned: Day {assignment.timeSlot.dayOfWeek}, 
                                    Period {assignment.timeSlot.period}
                                    {teacherConflict && 
                                      <span className="text-red-600 ml-2">
                                        (Teacher unavailable)
                                      </span>
                                    }
                                  </div>
                                )}
                              </div>
                            </li>
                          );
                        })}
                    </ul>
                  </div>
                )}
              </div>
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
