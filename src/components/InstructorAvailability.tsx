import React from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Grid, Clock } from 'lucide-react';
import { format, addWeeks, startOfWeek, endOfWeek, eachDayOfInterval } from 'date-fns';
import { useScheduleStore } from '../store/scheduleStore';
import type { InstructorAvailability as InstructorAvailabilityType } from '../types';

const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

export const InstructorAvailability: React.FC = () => {
  const { setInstructorAvailability, instructorAvailability } = useScheduleStore();
  const [currentWeek, setCurrentWeek] = React.useState(new Date());
  const [hoverControl, setHoverControl] = React.useState<{ type: 'day' | 'period', index: number } | null>(null);
  
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

  // Helper function to set a single period's availability
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
  
  // Toggle all periods for a specific day
  const toggleEntireDay = (date: Date, makeUnavailable?: boolean) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    const dayAvailability = instructorAvailability.find(a => a.date === dateStr);
    
    // Determine if we're making slots unavailable or available
    // If makeUnavailable is not specified, toggle based on whether most periods are currently unavailable
    const shouldMakeUnavailable = makeUnavailable !== undefined ? 
      makeUnavailable : 
      !(dayAvailability && dayAvailability.periods.length > PERIODS.length / 2);
    
    setInstructorAvailability(prev => {
      const currentAvailability = prev.filter(a => a.date !== dateStr);
      
      if (shouldMakeUnavailable) {
        // Make all periods unavailable
        return [...currentAvailability, {
          date: dateStr,
          periods: [...PERIODS] // All periods
        }];
      }
      
      // Making all periods available (by removing the day entry)
      return currentAvailability;
    });
  };
  
  // Toggle a specific period across all days of the week
  const togglePeriodForWeek = (period: number, makeUnavailable?: boolean) => {
    // Count how many days in the week have this period marked unavailable
    const unavailableCount = weekDates.reduce((count, date) => 
      isUnavailable(date, period) ? count + 1 : count, 0);
    
    // Determine if we're making slots unavailable or available
    // If makeUnavailable is not specified, toggle based on whether most days are currently unavailable
    const shouldMakeUnavailable = makeUnavailable !== undefined ? 
      makeUnavailable : 
      unavailableCount <= weekDates.length / 2;
    
    // Create a new availability array
    setInstructorAvailability(prev => {
      let newAvailability: InstructorAvailabilityType[] = [...prev];
      
      // Process each day of the week
      weekDates.forEach(date => {
        const dateStr = format(date, 'yyyy-MM-dd');
        const dayIndex = newAvailability.findIndex(a => a.date === dateStr);
        
        if (shouldMakeUnavailable) {
          // Make this period unavailable for this day
          if (dayIndex === -1) {
            // Day doesn't exist yet, add it with just this period
            newAvailability.push({
              date: dateStr,
              periods: [period]
            });
          } else if (!newAvailability[dayIndex].periods.includes(period)) {
            // Day exists but period isn't marked unavailable yet
            newAvailability = [
              ...newAvailability.slice(0, dayIndex),
              {
                ...newAvailability[dayIndex],
                periods: [...newAvailability[dayIndex].periods, period]
              },
              ...newAvailability.slice(dayIndex + 1)
            ];
          }
        } else {
          // Make this period available for this day
          if (dayIndex !== -1) {
            // Remove this period from unavailable list
            const newPeriods = newAvailability[dayIndex].periods.filter(p => p !== period);
            
            if (newPeriods.length === 0) {
              // No periods left, remove the day
              newAvailability = newAvailability.filter(a => a.date !== dateStr);
            } else {
              // Update with remaining periods
              newAvailability = [
                ...newAvailability.slice(0, dayIndex),
                {
                  ...newAvailability[dayIndex],
                  periods: newPeriods
                },
                ...newAvailability.slice(dayIndex + 1)
              ];
            }
          }
        }
      });
      
      return newAvailability;
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
        <p className="text-sm text-gray-600 mt-2">
          Use <Grid size={14} className="inline ml-1 mr-1" /> to toggle all periods for a day, and
          <Clock size={14} className="inline ml-1 mr-1" /> to toggle the same period across all days.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead>
            <tr>
              <th className="border p-2">Period</th>
              {weekDates.map((date, dateIndex) => (
                <th key={date.toISOString()} className="border p-2">
                  <div className="flex justify-between items-center">
                    <span>{DAYS[date.getDay() - 1]}</span>
                    <button 
                      className={`p-1 rounded-full ${hoverControl?.type === 'day' && hoverControl.index === dateIndex ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleEntireDay(date);
                      }}
                      onMouseEnter={() => setHoverControl({ type: 'day', index: dateIndex })}
                      onMouseLeave={() => setHoverControl(null)}
                      title={`Toggle all periods for ${format(date, 'EEEE, MMM d')}`}
                    >
                      <Grid size={16} className="text-gray-600" />
                    </button>
                  </div>
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
                <td className="border p-2 font-medium">
                  <div className="flex justify-between items-center">
                    <span>{period}</span>
                    <button 
                      className={`p-1 rounded-full ${hoverControl?.type === 'period' && hoverControl.index === period ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        togglePeriodForWeek(period);
                      }}
                      onMouseEnter={() => setHoverControl({ type: 'period', index: period })}
                      onMouseLeave={() => setHoverControl(null)}
                      title={`Toggle period ${period} for all days`}
                    >
                      <Clock size={16} className="text-gray-600" />
                    </button>
                  </div>
                </td>
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
