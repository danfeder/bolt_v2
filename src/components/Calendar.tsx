import React from 'react';
import { useScheduleStore } from '../store/scheduleStore';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import { format, addWeeks, subWeeks, startOfWeek, eachDayOfInterval, endOfWeek, isWithinInterval, startOfDay } from 'date-fns';

const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);

export const Calendar: React.FC = () => {
  const { assignments, classes, constraints } = useScheduleStore();
  const [currentWeek, setCurrentWeek] = React.useState(() => 
    new Date(constraints.startDate)
  );

  // Calculate the date range for the schedule, using startOfDay to ignore time
  const scheduleInterval = {
    start: startOfDay(new Date(constraints.startDate)),
    end: startOfDay(new Date(constraints.endDate))
  };

  // Get the dates for the current week (Mon-Fri)
  const weekDates = React.useMemo(() => {
    const start = startOfWeek(currentWeek, { weekStartsOn: 1 }); // Start on Monday
    const end = endOfWeek(start, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end }).slice(0, 5); // Only Mon-Fri
  }, [currentWeek]);

  const getAssignments = (date: Date, period: number) => {
    return assignments.filter(a => {
      const assignmentDate = new Date(a.date);
      return startOfDay(assignmentDate).getTime() === startOfDay(date).getTime() && 
             a.timeSlot.period === period;
    });
  };

  const getClassName = (classId: string) => {
    return classes.find(c => c.id === classId)?.name || 'Unknown';
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    setCurrentWeek(current => {
      const newDate = direction === 'prev' 
        ? subWeeks(current, 1) 
        : addWeeks(current, 1);
      
      // Ensure we stay within the schedule range
      if (!isWithinInterval(startOfDay(newDate), scheduleInterval)) {
        return current;
      }
      return newDate;
    });
  };

  const isDateInRange = (date: Date) => {
    return isWithinInterval(startOfDay(date), scheduleInterval);
  };

  return (
    <div className="overflow-x-auto">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <CalendarIcon className="text-blue-500" />
            Gym Class Schedule
          </h2>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigateWeek('prev')}
              disabled={!isDateInRange(subWeeks(currentWeek, 1))}
              className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={20} />
            </button>
            <span className="font-medium">
              Week of {format(weekDates[0], 'MMM d, yyyy')}
            </span>
            <button
              onClick={() => navigateWeek('next')}
              disabled={!isDateInRange(addWeeks(currentWeek, 1))}
              className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-200">
            <thead>
              <tr>
                <th className="border p-2">Period</th>
                {weekDates.map(date => (
                  <th key={date.toISOString()} className="border p-2">
                    <div>{format(date, 'EEEE')}</div>
                    <div className="text-sm text-gray-500">
                      {format(date, 'MMM d')}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {PERIODS.map(period => (
                <tr key={period}>
                  <td className="border p-2 font-medium">{period}</td>
                  {weekDates.map(date => {
                    const dateAssignments = getAssignments(date, period);
                    const isInScheduleRange = isDateInRange(date);
                    return (
                      <td
                        key={date.toISOString()}
                        className={`border p-2 ${!isInScheduleRange ? 'bg-gray-50' : ''}`}
                      >
                        {isInScheduleRange && dateAssignments.map(assignment => (
                          <div key={assignment.classId} className="p-2 bg-blue-50 rounded">
                            <div className="font-medium">
                              {getClassName(assignment.classId)}
                            </div>
                          </div>
                        ))}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-sm text-gray-500">
          Schedule period: {format(scheduleInterval.start, 'MMM d, yyyy')} - {format(scheduleInterval.end, 'MMM d, yyyy')}
        </div>
      </div>
    </div>
  );
};