import React, { useState, useEffect } from 'react';
import { useSimplifiedScheduler } from '../../store/simplifiedSchedulerStore';
import { PriorityList } from './PriorityList';
import { InstructorLoadSettings } from './InstructorLoadSettings';
import { AdvancedOptions } from './AdvancedOptions';
import { Priority, InstructorLoadSettings as ILoadSettings, AdvancedSettings } from './types';

/**
 * Simplified scheduler configuration panel designed for non-technical users
 * Provides an intuitive interface for setting scheduling priorities and constraints
 * 
 * Integration with the scheduling system:
 * - Maps priority order to solver weights
 * - Connects instructor load settings to scheduler constraints
 * - Provides advanced tuning options for special cases
 */
export const SimplifiedSchedulerPanel: React.FC = () => {
  // Use our simplified connector instead of the raw store
  const { isGenerating, error, constraints, generateSchedule } = useSimplifiedScheduler();
  
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
  
  // Initialize instructor load settings from current constraints if available
  useEffect(() => {
    if (constraints) {
      setInstructorLoad({
        ...instructorLoad,
        maxPerDay: constraints.maxClassesPerDay || instructorLoad.maxPerDay,
        maxPerWeek: constraints.maxClassesPerWeek || instructorLoad.maxPerWeek,
        minPerWeek: constraints.minPeriodsPerWeek || instructorLoad.minPerWeek,
        allowMaxFlexibility: constraints.consecutiveClassesRule === 'soft'
      });
    }
  }, [constraints]);

  // Handle priority reordering
  const handlePriorityReorder = (newPriorities: Priority[]) => {
    setPriorities(newPriorities);
  };
  
  // Handle instructor load changes
  const handleInstructorLoadChange = (changes: Partial<ILoadSettings>) => {
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
  const handleGenerateSchedule = async () => {
    try {
      // Use our connector to generate the schedule with our simplified configuration
      await generateSchedule(priorities, instructorLoad, advanced);
      
      // In a future increment, we'll add more detailed UI feedback
      console.log('Schedule generation completed successfully');
    } catch (err) {
      console.error('Error generating schedule:', err);
    }
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
      
      {error && !isGenerating && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-red-700">
            {error}
          </p>
        </div>
      )}
    </div>
  );
};
