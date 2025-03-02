import React, { useState } from 'react';
import { Info, AlertCircle } from 'lucide-react';
import type { ScheduleAssignment, Class } from '../../types';
import { useScheduleStore } from '../../store/scheduleStore';

interface ClassAssignmentCardProps {
  assignment: ScheduleAssignment;
}

export const ClassAssignmentCard: React.FC<ClassAssignmentCardProps> = ({ assignment }) => {
  const [showDetails, setShowDetails] = useState(false);
  const { classes } = useScheduleStore();
  
  // Find the class details
  const classDetails = classes.find(c => c.name === assignment.name);
  
  // Check if this assignment conflicts with any periods for this class
  const hasConflict = classDetails?.conflicts.some(
    conflict => 
      conflict.dayOfWeek === assignment.timeSlot.dayOfWeek && 
      conflict.period === assignment.timeSlot.period
  );
  
  // Check if this is a required period
  const isRequired = classDetails?.required_periods.some(
    required => {
      const requiredDate = new Date(required.date);
      const assignmentDate = new Date(assignment.date);
      return (
        requiredDate.getFullYear() === assignmentDate.getFullYear() &&
        requiredDate.getMonth() === assignmentDate.getMonth() &&
        requiredDate.getDate() === assignmentDate.getDate() &&
        required.period === assignment.timeSlot.period
      );
    }
  );
  
  // Get grade level from class details
  const grade = classDetails?.grade || '';
  
  // Generate a background color based on grade
  const getGradeColor = (grade: string) => {
    switch(grade) {
      case 'K': return 'bg-red-50 border-red-200';
      case '1': return 'bg-orange-50 border-orange-200';
      case '2': return 'bg-yellow-50 border-yellow-200';
      case '3': return 'bg-green-50 border-green-200';
      case '4': return 'bg-teal-50 border-teal-200';
      case '5': return 'bg-blue-50 border-blue-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };
  
  return (
    <div 
      className={`p-2 rounded border ${getGradeColor(grade)} transition-all relative 
        ${hasConflict ? 'ring-2 ring-red-400' : ''} 
        ${isRequired ? 'ring-2 ring-green-400' : ''}`}
    >
      <div className="flex items-start justify-between">
        <div className="font-medium">
          {assignment.name}
          {grade && <span className="ml-1 text-gray-500 text-sm">({grade})</span>}
        </div>
        
        {/* Status indicators */}
        <div className="flex">
          {hasConflict && (
            <span className="text-red-500" title="This assignment has a conflict">
              <AlertCircle size={16} />
            </span>
          )}
          
          <button 
            onClick={() => setShowDetails(!showDetails)}
            className="ml-1 text-gray-400 hover:text-gray-600"
            aria-label={showDetails ? "Hide details" : "Show details"}
          >
            <Info size={16} />
          </button>
        </div>
      </div>
      
      {/* Expanded details */}
      {showDetails && (
        <div className="mt-2 text-sm text-gray-600 border-t pt-1">
          <div className="grid grid-cols-2 gap-x-2">
            <span className="text-gray-500">Period:</span>
            <span>{assignment.timeSlot.period}</span>
            
            <span className="text-gray-500">Status:</span>
            <span>
              {hasConflict && <span className="text-red-500">Conflict</span>}
              {isRequired && <span className="text-green-500">Required</span>}
              {!hasConflict && !isRequired && <span>Normal</span>}
            </span>
            
            {classDetails && (
              <>
                <span className="text-gray-500">Conflicts:</span>
                <span>{classDetails.conflicts.length}</span>
                
                <span className="text-gray-500">Required:</span>
                <span>{classDetails.required_periods.length}</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
