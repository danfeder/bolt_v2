import React from 'react';
import { ChevronLeft, ChevronRight, Calendar, List, Download } from 'lucide-react';
import { format, addWeeks, subWeeks, isWithinInterval, startOfDay } from 'date-fns';
import { ViewMode } from './index';

interface ScheduleHeaderProps {
  viewMode: ViewMode;
  onViewModeChange: () => void;
  scheduleInterval: { start: Date; end: Date };
  currentWeek: Date;
  setCurrentWeek: React.Dispatch<React.SetStateAction<Date>>;
}

export const ScheduleHeader: React.FC<ScheduleHeaderProps> = ({
  viewMode,
  onViewModeChange,
  scheduleInterval,
  currentWeek,
  setCurrentWeek
}) => {
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

  const handleExport = () => {
    // Export functionality will be implemented in Phase 4
    alert('Export functionality coming soon!');
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
      <h2 className="text-xl font-semibold flex items-center gap-2">
        <Calendar className="text-blue-500" />
        Gym Class Schedule
      </h2>
      
      <div className="flex flex-wrap items-center gap-4">
        {viewMode === 'calendar' && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigateWeek('prev')}
              disabled={!isDateInRange(subWeeks(currentWeek, 1))}
              className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Previous week"
            >
              <ChevronLeft size={20} />
            </button>
            <span className="font-medium whitespace-nowrap">
              Week of {format(currentWeek, 'MMM d, yyyy')}
            </span>
            <button
              onClick={() => navigateWeek('next')}
              disabled={!isDateInRange(addWeeks(currentWeek, 1))}
              className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Next week"
            >
              <ChevronRight size={20} />
            </button>
          </div>
        )}
        
        <div className="flex items-center gap-2">
          <button
            onClick={onViewModeChange}
            className="px-3 py-2 rounded-md bg-blue-50 hover:bg-blue-100 text-blue-700 flex items-center gap-1"
            aria-label={viewMode === 'calendar' ? 'Switch to list view' : 'Switch to calendar view'}
          >
            {viewMode === 'calendar' ? (
              <>
                <List size={16} />
                <span>List View</span>
              </>
            ) : (
              <>
                <Calendar size={16} />
                <span>Calendar View</span>
              </>
            )}
          </button>
          
          <button
            onClick={handleExport}
            className="px-3 py-2 rounded-md bg-gray-50 hover:bg-gray-100 text-gray-700 flex items-center gap-1"
            aria-label="Export schedule"
          >
            <Download size={16} />
            <span>Export</span>
          </button>
        </div>
      </div>
    </div>
  );
};
