import React, { useState } from 'react';
import { Search, ChevronDown, ChevronUp, Filter } from 'lucide-react';
import { FilterState } from './index';
import { useScheduleStore } from '../../store/scheduleStore';

interface ScheduleFilterPanelProps {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
}

export const ScheduleFilterPanel: React.FC<ScheduleFilterPanelProps> = ({
  filters,
  setFilters
}) => {
  const [expanded, setExpanded] = useState(false);
  const { classes } = useScheduleStore();
  
  // Extract all available grades from classes
  const availableGrades = React.useMemo(() => {
    const grades = new Set(classes.map(c => c.grade));
    return Array.from(grades).sort();
  }, [classes]);
  
  // Toggle period filter
  const togglePeriod = (period: number) => {
    setFilters(prev => {
      const newPeriods = prev.periods.includes(period)
        ? prev.periods.filter(p => p !== period)
        : [...prev.periods, period];
      return { ...prev, periods: newPeriods };
    });
  };
  
  // Toggle grade filter
  const toggleGrade = (grade: string) => {
    setFilters(prev => {
      const newGrades = prev.grades.includes(grade)
        ? prev.grades.filter(g => g !== grade)
        : [...prev.grades, grade];
      return { ...prev, grades: newGrades };
    });
  };
  
  // Toggle conflicts filter
  const toggleConflicts = () => {
    setFilters(prev => ({
      ...prev,
      showConflicts: !prev.showConflicts
    }));
  };
  
  // Handle search input
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters(prev => ({
      ...prev,
      searchQuery: e.target.value
    }));
  };
  
  return (
    <div className="bg-gray-50 rounded-lg p-3 transition-all">
      <div className="flex items-center justify-between">
        <h3 className="text-md font-medium flex items-center gap-2">
          <Filter size={18} />
          Filters & Search
        </h3>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-500 hover:text-gray-700"
          aria-label={expanded ? "Collapse filters" : "Expand filters"}
        >
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>
      
      {/* Search input - always visible */}
      <div className="mt-2 relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={16} className="text-gray-400" />
        </div>
        <input
          type="text"
          placeholder="Search by class name..."
          value={filters.searchQuery}
          onChange={handleSearchChange}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
        />
      </div>
      
      {/* Expanded filters */}
      {expanded && (
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          {/* Period filters */}
          <div>
            <h4 className="text-sm font-medium mb-2">Periods</h4>
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 8 }, (_, i) => i + 1).map(period => (
                <button
                  key={period}
                  onClick={() => togglePeriod(period)}
                  className={`px-3 py-1 text-sm rounded-full 
                    ${filters.periods.includes(period) 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-gray-200 text-gray-700'}`}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
          
          {/* Grade filters */}
          <div>
            <h4 className="text-sm font-medium mb-2">Grades</h4>
            <div className="flex flex-wrap gap-2">
              {availableGrades.map(grade => (
                <button
                  key={grade}
                  onClick={() => toggleGrade(grade)}
                  className={`px-3 py-1 text-sm rounded-full 
                    ${filters.grades.includes(grade) 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-gray-200 text-gray-700'}`}
                >
                  {grade}
                </button>
              ))}
            </div>
          </div>
          
          {/* Additional filters */}
          <div className="sm:col-span-2">
            <h4 className="text-sm font-medium mb-2">Additional Filters</h4>
            <div className="flex items-center gap-3">
              <label className="inline-flex items-center">
                <input
                  type="checkbox"
                  checked={filters.showConflicts}
                  onChange={toggleConflicts}
                  className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                />
                <span className="ml-2 text-sm text-gray-700">Show only conflicts</span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
