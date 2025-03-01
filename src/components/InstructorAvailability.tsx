import React from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-react';
import { format, addWeeks, startOfWeek, endOfWeek, eachDayOfInterval } from 'date-fns';
import { useScheduleStore } from '../store/scheduleStore';

const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

export const InstructorAvailability: React.FC = () => {
  const { setInstructorAvailability, instructorAvailability } = useScheduleStore();
  const [currentWeek, setCurrentWeek] = React.useState(new Date());
  
  const weekDates = React.useMemo(() => {
    const start = startOfWeek(currentWeek, { weekStartsOn: 1 });
    const end = endOfWeek(currentWeek, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end }).slice(0, 5); // Monday to Friday
  }, [currentWeek]);

  const isUnavailable = (date: Date, period: number): boolean => {
    const dateStr = format(date, 'yyyy-MM-dd');
    const dayAvailability = instructorAvailability.find(a => a.date === dateStr);
    return dayAvailability?.periods.includes(period) || false;
  };

  const toggleSlot = (date: Date, period: number) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    const isCurrentlyUnavailable = isUnavailable(date, period);

    setInstructorAvailability(prev => {
      const currentAvailability = [...prev];
      const dayIndex = currentAvailability.findIndex(a => a.date === dateStr);
      
      // Initialize day if it doesn't exist
      if (dayIndex === -1) {
        if (!isCurrentlyUnavailable) {
          return [...currentAvailability, {
            date: dateStr,
            periods: [period]
          }];
        }
        return currentAvailability;
      }

      const day = { ...currentAvailability[dayIndex] };
      
      if (isCurrentlyUnavailable) {
        // Remove period from unavailable list
        day.periods = day.periods.filter(p => p !== period);
        // If no periods left, remove the day entry
        if (day.periods.length === 0) {
          return currentAvailability.filter(a => a.date !== dateStr);
        }
      } else {
        // Add period to unavailable list
        day.periods = [...day.periods, period];
      }

      return [
        ...currentAvailability.slice(0, dayIndex),
        day,
        ...currentAvailability.slice(dayIndex + 1)
      ];
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <CalendarIcon className="text-blue-500" />
          Set Your Unavailable Times
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentWeek(prev => addWeeks(prev, -1))}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ChevronLeft />
          </button>
          <span className="font-medium">
            Week of {format(weekDates[0], 'MMM d, yyyy')}
          </span>
          <button
            onClick={() => setCurrentWeek(prev => addWeeks(prev, 1))}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ChevronRight />
          </button>
        </div>
      </div>

      <div className="bg-blue-50 p-4 rounded-lg mb-6">
        <p className="text-sm text-gray-600">
          Click cells to toggle between states:
          <span className="inline-flex items-center gap-2 ml-2">
            <span className="w-4 h-4 bg-gray-50 rounded"></span> Available
            <span className="w-4 h-4 bg-red-100 rounded"></span> Unavailable
          </span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead>
            <tr>
              <th className="border p-2">Period</th>
              {weekDates.map(date => (
                <th key={date.toISOString()} className="border p-2">
                  <div>{DAYS[date.getDay() - 1]}</div>
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
                {weekDates.map(date => (
                  <td
                    key={date.toISOString()}
                    className="border p-2"
                    onClick={() => toggleSlot(date, period)}
                  >
                    <div
                      className={`w-full h-8 rounded cursor-pointer transition-colors ${
                        isUnavailable(date, period)
                          ? 'bg-red-100 hover:bg-red-200'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
