import React, { useState } from 'react';
import { useScheduleStore } from '../../store/scheduleStore';
import { PriorityList } from './PriorityList';
import { InstructorLoadSettings } from './InstructorLoadSettings';
import { AdvancedOptions } from './AdvancedOptions';

// Types for our simplified scheduler
export interface Priority {
  id: string;
  name: string;
  description: string;
}

export interface InstructorLoadSettings {
  minPerDay: number;
  maxPerDay: number;
  minPerWeek: number;
  maxPerWeek: number;
  allowMinFlexibility: boolean;
  allowMaxFlexibility: boolean;
}

export interface AdvancedSettings {
  autoTuneWeights: boolean;
  requireBreakBetweenClasses: boolean;
}

/**
 * Simplified scheduler configuration panel designed for non-technical users
 * Provides an intuitive interface for setting scheduling priorities and constraints
 */
export const SimplifiedSchedulerPanel: React.FC = () => {
  const isGenerating = useScheduleStore(state => state.isGenerating);
  const generateSchedule = useScheduleStore(state => state.generateSchedule);
  
  // Default priority order
  const [priorities, setPriorities] = useState([
    { id: 'grade_grouping', name: 'Grade Grouping', description: 'Keep similar grades together' },
    { id: 'weekly_balance', name: 'Weekly Balance', description: 'Distribute classes evenly across weekdays' },
    { id: 'daily_spacing', name: 'Daily Spacing', description: 'Spread classes throughout each day' },
    { id: 'preferred_periods', name: 'Preferred Times', description: 'Schedule during desired time slots' }
  ]);
  
  // Instructor load settings
  const [instructorLoad, setInstructorLoad] = useState({
    minPerDay: 1,
    maxPerDay: 3,
    minPerWeek: 5,
    maxPerWeek: 15,
    allowMinFlexibility: true,
    allowMaxFlexibility: false
  });
  
  // Advanced settings
  const [advanced, setAdvanced] = useState({
    autoTuneWeights: false,
    requireBreakBetweenClasses: true
  });
  
  // Handle priority reordering
  const handlePriorityReorder = (newPriorities: Priority[]) => {
    setPriorities(newPriorities);
  };
  
  // Handle instructor load changes
  const handleInstructorLoadChange = (changes: Partial<InstructorLoadSettings>) => {
    setInstructorLoad({
      ...instructorLoad,
      ...changes
    });
  };
  
  // Handle advanced setting changes
  const handleAdvancedChange = (changes: Partial<AdvancedSettings>) => {
    setAdvanced({
      ...advanced,
      ...changes
    });
  };
  
  // Generate schedule
  const handleGenerateSchedule = () => {
    // Convert priorities to weights
    const weights: Record<string, number> = {};
    priorities.forEach((priority, index) => {
      // Higher index = lower in the list = lower weight
      const weight = 4000 - (index * 1000);
      weights[priority.id] = weight;
    });
    
    // In the next increment, we'll integrate this with the store
    // For now we'll use the existing generateSchedule function with no arguments
    // which will maintain compatibility with the existing system
    generateSchedule();
    
    // Log the configuration for debugging/verification
    console.log('Simplified scheduler configuration:', {
      priorities: priorities.map(p => p.name),
      instructorLoad,
      advanced
    });
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Schedule Settings</h2>
      
      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-700 mb-2">Schedule Priorities</h3>
        <p className="text-sm text-gray-500 mb-4">
          Drag to reorder. Items at the top have higher priority.
        </p>
        
        <PriorityList 
          priorities={priorities} 
          onReorder={handlePriorityReorder}
          disabled={isGenerating}
        />
      </div>
      
      <div className="border-t border-gray-200 my-6 pt-6">
        <InstructorLoadSettings
          settings={instructorLoad}
          onChange={handleInstructorLoadChange}
          disabled={isGenerating}
        />
      </div>
      
      <div className="border-t border-gray-200 my-6 pt-6">
        <AdvancedOptions
          settings={advanced}
          onChange={handleAdvancedChange}
          disabled={isGenerating}
        />
      </div>
      
      <div className="mt-8 flex justify-center">
        <button
          onClick={handleGenerateSchedule}
          disabled={isGenerating}
          className={`
            px-6 py-3 rounded-md text-white font-medium text-lg
            ${isGenerating 
              ? 'bg-blue-300 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 shadow-sm'
            }
          `}
        >
          {isGenerating ? 'Generating Schedule...' : 'Generate Schedule'}
        </button>
      </div>
      
      {isGenerating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-blue-700">
            Creating your schedule. This may take a moment depending on the complexity.
          </p>
        </div>
      )}
    </div>
  );
};
