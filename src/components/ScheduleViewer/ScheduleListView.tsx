import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ArrowUpDown } from 'lucide-react';
import type { ScheduleAssignment } from '../../types';
import { format } from 'date-fns';
import { ClassAssignmentCard } from './ClassAssignmentCard';
import { useScheduleStore } from '../../store/scheduleStore';

interface ScheduleListViewProps {
  filteredAssignments: ScheduleAssignment[];
}

type SortField = 'date' | 'period' | 'name' | 'grade';
type SortDirection = 'asc' | 'desc';

export const ScheduleListView: React.FC<ScheduleListViewProps> = ({
  filteredAssignments
}) => {
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const { classes } = useScheduleStore();
  
  // Handle sort column click
  const handleSort = (field: SortField) => {
    if (field === sortField) {
      // Toggle direction if same field
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to ascending
      setSortField(field);
      setSortDirection('asc');
    }
  };
  
  // Sort the assignments
  const sortedAssignments = useMemo(() => {
    return [...filteredAssignments].sort((a, b) => {
      const sortMultiplier = sortDirection === 'asc' ? 1 : -1;
      
      switch (sortField) {
        case 'date':
          return sortMultiplier * (new Date(a.date).getTime() - new Date(b.date).getTime());
        
        case 'period':
          return sortMultiplier * (a.timeSlot.period - b.timeSlot.period);
        
        case 'name':
          return sortMultiplier * a.name.localeCompare(b.name);
          
        case 'grade':
          const aClass = classes.find(c => c.name === a.name);
          const bClass = classes.find(c => c.name === b.name);
          return sortMultiplier * (aClass?.grade || '').localeCompare(bClass?.grade || '');
          
        default:
          return 0;
      }
    });
  }, [filteredAssignments, sortField, sortDirection, classes]);
  
  // Group assignments by date for better display
  const groupedAssignments = useMemo(() => {
    const groups: { [key: string]: ScheduleAssignment[] } = {};
    
    sortedAssignments.forEach(assignment => {
      if (!groups[assignment.date]) {
        groups[assignment.date] = [];
      }
      groups[assignment.date].push(assignment);
    });
    
    return Object.entries(groups).sort(([dateA], [dateB]) => {
      const sortMultiplier = sortField === 'date' && sortDirection === 'asc' ? 1 : -1;
      return sortMultiplier * (new Date(dateA).getTime() - new Date(dateB).getTime());
    });
  }, [sortedAssignments, sortField, sortDirection]);
  
  // Render sort indicator
  const renderSortIndicator = (field: SortField) => {
    if (field !== sortField) {
      return <ArrowUpDown size={14} className="ml-1 opacity-50" />;
    }
    
    return sortDirection === 'asc' 
      ? <ChevronUp size={14} className="ml-1" data-testid={`sort-indicator-${field}`} />
      : <ChevronDown size={14} className="ml-1" data-testid={`sort-indicator-${field}`} />;
  };
  
  if (filteredAssignments.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No assignments match your filters.
      </div>
    );
  }
  
  return (
    <div>
      <div className="overflow-hidden mb-4">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('date')}
              >
                <div className="flex items-center">
                  Date
                  {renderSortIndicator('date')}
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('period')}
              >
                <div className="flex items-center">
                  Period
                  {renderSortIndicator('period')}
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center">
                  Class
                  {renderSortIndicator('name')}
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('grade')}
              >
                <div className="flex items-center">
                  Grade
                  {renderSortIndicator('grade')}
                </div>
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Details
              </th>
            </tr>
          </thead>
        </table>
      </div>
      
      <div className="space-y-6">
        {groupedAssignments.map(([date, assignments]) => (
          <div key={date} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="bg-gray-100 px-4 py-2 font-medium">
              {format(new Date(date), 'EEEE, MMMM d, yyyy')}
              <span className="ml-2 text-sm text-gray-500">
                ({assignments.length} classes)
              </span>
            </div>
            
            <div className="divide-y divide-gray-200">
              {assignments.map(assignment => (
                <div 
                  key={`${assignment.date}-${assignment.timeSlot.period}-${assignment.name}`}
                  className="p-4 hover:bg-gray-50"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="w-16 flex-shrink-0">
                      <div className="text-center">
                        <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-800 font-medium">
                          {assignment.timeSlot.period}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex-grow">
                      <ClassAssignmentCard assignment={assignment} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
