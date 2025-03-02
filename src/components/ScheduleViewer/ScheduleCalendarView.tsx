import React, { useMemo } from 'react';
import { format, startOfWeek, endOfWeek, eachDayOfInterval, startOfDay } from 'date-fns';
import type { ScheduleAssignment } from '../../types';
import { ClassAssignmentCard } from './ClassAssignmentCard';

const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);

interface ScheduleCalendarViewProps {
  filteredAssignments: ScheduleAssignment[];
  currentWeek: Date;
  setCurrentWeek: React.Dispatch<React.SetStateAction<Date>>;
  scheduleInterval: { start: Date; end: Date };
}

export const ScheduleCalendarView: React.FC<ScheduleCalendarViewProps> = ({
  filteredAssignments,
  currentWeek,
  scheduleInterval
}) => {
  // Get the dates for the current week (Mon-Fri)
  const weekDates = useMemo(() => {
    const start = startOfWeek(currentWeek, { weekStartsOn: 1 }); // Start on Monday
    const end = endOfWeek(start, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end }).slice(0, 5); // Only Mon-Fri
  }, [currentWeek]);

  const getAssignments = (date: Date, period: number) => {
    return filteredAssignments.filter(a => {
      const assignmentDate = new Date(a.date);
      return startOfDay(assignmentDate).getTime() === startOfDay(date).getTime() && 
             a.timeSlot.period === period;
    });
  };

  const isDateInRange = (date: Date) => {
    return date >= scheduleInterval.start && date <= scheduleInterval.end;
  };

  // Calculate total assignments by day for visual indicators
  const assignmentsByDay = useMemo(() => {
    const result: Record<string, number> = {};
    weekDates.forEach(date => {
      const dateStr = format(date, 'yyyy-MM-dd');
      const count = filteredAssignments.filter(a => a.date === dateStr).length;
      result[dateStr] = count;
    });
    return result;
  }, [filteredAssignments, weekDates]);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-200">
        <thead>
          <tr>
            <th className="border p-2 bg-gray-50">Period</th>
            {weekDates.map(date => {
              const dateStr = format(date, 'yyyy-MM-dd');
              const count = assignmentsByDay[dateStr] || 0;
              const isActive = isDateInRange(date);
              return (
                <th 
                  key={date.toISOString()} 
                  className={`border p-2 ${isActive ? 'bg-white' : 'bg-gray-50'}`}
                >
                  <div>{format(date, 'EEEE')}</div>
                  <div className="text-sm text-gray-500 flex items-center justify-center gap-1">
                    {format(date, 'MMM d')}
                    {count > 0 && isActive && (
                      <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        {count}
                      </span>
                    )}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {PERIODS.map(period => (
            <tr key={period}>
              <td className="border p-2 font-medium bg-gray-50">{period}</td>
              {weekDates.map(date => {
                const dateAssignments = getAssignments(date, period);
                const isInScheduleRange = isDateInRange(date);
                const hasAssignments = dateAssignments.length > 0;
                
                return (
                  <td
                    key={date.toISOString()}
                    className={`border p-2 min-w-[150px] ${!isInScheduleRange ? 'bg-gray-50' : ''} 
                        ${hasAssignments ? 'bg-blue-50' : ''}`}
                  >
                    {isInScheduleRange && dateAssignments.map(assignment => (
                      <ClassAssignmentCard 
                        key={`${assignment.date}-${assignment.timeSlot.period}-${assignment.name}`}
                        assignment={assignment}
                      />
                    ))}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
