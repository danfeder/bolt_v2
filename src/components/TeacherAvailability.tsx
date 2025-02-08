import React from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-react';
import { format, addWeeks, startOfWeek, endOfWeek, eachDayOfInterval } from 'date-fns';
import { useScheduleStore } from '../store/scheduleStore';
import type { TimeSlot } from '../types';

const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

type SlotState = 'blank' | 'unavailable' | 'preferred' | 'avoid';

export const TeacherAvailability: React.FC = () => {
  const { setTeacherAvailability, teacherAvailability } = useScheduleStore();
  const [currentWeek, setCurrentWeek] = React.useState(new Date());
  
  const weekDates = React.useMemo(() => {
    const start = startOfWeek(currentWeek, { weekStartsOn: 1 });
    const end = endOfWeek(currentWeek, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end }).slice(0, 5); // Monday to Friday
  }, [currentWeek]);

  const getSlotState = (date: Date, period: number): SlotState => {
    const dateStr = format(date, 'yyyy-MM-dd');
    const dayAvailability = teacherAvailability.find(a => a.date === dateStr);
    
    if (!dayAvailability) return 'blank';

    if (dayAvailability.unavailableSlots.some(slot => 
      slot.dayOfWeek === date.getDay() && slot.period === period
    )) {
      return 'unavailable';
    }

    if (dayAvailability.preferredSlots.some(slot => 
      slot.dayOfWeek === date.getDay() && slot.period === period
    )) {
      return 'preferred';
    }

    if (dayAvailability.avoidSlots.some(slot => 
      slot.dayOfWeek === date.getDay() && slot.period === period
    )) {
      return 'avoid';
    }

    return 'blank';
  };

  const toggleSlot = (date: Date, period: number) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    const dayOfWeek = date.getDay();
    const newSlot: TimeSlot = { dayOfWeek, period };
    const currentState = getSlotState(date, period);

    setTeacherAvailability(prev => {
      const currentAvailability = [...prev];
      const dayIndex = currentAvailability.findIndex(a => a.date === dateStr);
      
      // Initialize day if it doesn't exist
      if (dayIndex === -1) {
        return [...currentAvailability, {
          date: dateStr,
          unavailableSlots: currentState === 'blank' ? [newSlot] : [],
          preferredSlots: [],
          avoidSlots: []
        }];
      }

      const day = { ...currentAvailability[dayIndex] };

      // Update slots based on current state
      switch (currentState) {
        case 'blank':
          // Blank → Unavailable
          day.unavailableSlots = [...day.unavailableSlots, newSlot];
          break;
        case 'unavailable':
          // Unavailable → Preferred
          day.unavailableSlots = day.unavailableSlots.filter(
            s => !(s.dayOfWeek === dayOfWeek && s.period === period)
          );
          day.preferredSlots = [...day.preferredSlots, newSlot];
          break;
        case 'preferred':
          // Preferred → Avoid
          day.preferredSlots = day.preferredSlots.filter(
            s => !(s.dayOfWeek === dayOfWeek && s.period === period)
          );
          day.avoidSlots = [...day.avoidSlots, newSlot];
          break;
        case 'avoid':
          // Avoid → Blank
          day.avoidSlots = day.avoidSlots.filter(
            s => !(s.dayOfWeek === dayOfWeek && s.period === period)
          );
          break;
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
            <span className="w-4 h-4 bg-green-100 rounded"></span> Preferred
            <span className="w-4 h-4 bg-purple-100 rounded"></span> Avoid
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
                        getSlotState(date, period) === 'unavailable'
                          ? 'bg-red-100 hover:bg-red-200'
                          : getSlotState(date, period) === 'preferred'
                          ? 'bg-green-100 hover:bg-green-200'
                          : getSlotState(date, period) === 'avoid'
                          ? 'bg-purple-100 hover:bg-purple-200'
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