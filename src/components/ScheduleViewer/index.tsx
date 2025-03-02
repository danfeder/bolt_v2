import React, { useState } from 'react';
import { ScheduleHeader } from './ScheduleHeader';
import { ScheduleCalendarView } from './ScheduleCalendarView';
import { ScheduleListView } from './ScheduleListView';
import { ScheduleFilterPanel } from './ScheduleFilterPanel';
import { useScheduleStore } from '../../store/scheduleStore';
import { format, startOfDay } from 'date-fns';

export type ViewMode = 'calendar' | 'list';
export type FilterState = {
  dateRange: [Date, Date];
  periods: number[];
  grades: string[];
  searchQuery: string;
  showConflicts: boolean;
};

export const ScheduleViewer: React.FC = () => {
  const { assignments, constraints } = useScheduleStore();
  const [viewMode, setViewMode] = useState<ViewMode>('calendar');
  const [currentWeek, setCurrentWeek] = useState(() => 
    new Date(constraints.startDate)
  );
  
  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    dateRange: [
      new Date(constraints.startDate),
      new Date(constraints.endDate)
    ],
    periods: Array.from({ length: 8 }, (_, i) => i + 1),
    grades: [],
    searchQuery: '',
    showConflicts: false
  });
  
  // Calculate the date range for the schedule
  const scheduleInterval = {
    start: startOfDay(new Date(constraints.startDate)),
    end: startOfDay(new Date(constraints.endDate))
  };
  
  // Toggle between calendar and list view
  const toggleViewMode = () => {
    setViewMode(viewMode === 'calendar' ? 'list' : 'calendar');
  };
  
  // Apply filters to assignments
  const filteredAssignments = React.useMemo(() => {
    return assignments.filter(assignment => {
      const assignmentDate = new Date(assignment.date);
      
      // Filter by date range
      if (
        assignmentDate < filters.dateRange[0] ||
        assignmentDate > filters.dateRange[1]
      ) {
        return false;
      }
      
      // Filter by period
      if (!filters.periods.includes(assignment.timeSlot.period)) {
        return false;
      }
      
      // Filter by search query
      if (
        filters.searchQuery &&
        !assignment.name.toLowerCase().includes(filters.searchQuery.toLowerCase())
      ) {
        return false;
      }
      
      // Filter by grade (requires looking up class information)
      // Will be implemented when we have grade information in assignments
      
      return true;
    });
  }, [assignments, filters]);
  
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <ScheduleHeader 
        viewMode={viewMode}
        onViewModeChange={toggleViewMode}
        scheduleInterval={scheduleInterval}
        currentWeek={currentWeek}
        setCurrentWeek={setCurrentWeek}
      />
      
      <div className="mb-4">
        <ScheduleFilterPanel 
          filters={filters}
          setFilters={setFilters}
        />
      </div>
      
      <div className="mt-4">
        {viewMode === 'calendar' ? (
          <ScheduleCalendarView 
            filteredAssignments={filteredAssignments}
            currentWeek={currentWeek}
            setCurrentWeek={setCurrentWeek}
            scheduleInterval={scheduleInterval}
          />
        ) : (
          <ScheduleListView 
            filteredAssignments={filteredAssignments}
          />
        )}
      </div>
      
      <div className="mt-4 text-sm text-gray-500">
        Schedule period: {format(scheduleInterval.start, 'MMM d, yyyy')} - {format(scheduleInterval.end, 'MMM d, yyyy')}
      </div>
    </div>
  );
};

export default ScheduleViewer;
