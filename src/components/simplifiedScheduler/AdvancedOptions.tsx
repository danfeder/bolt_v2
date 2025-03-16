import React from 'react';
import { AdvancedSettings } from './types';

interface AdvancedOptionsProps {
  settings: AdvancedSettings;
  onChange: (changes: Partial<AdvancedSettings>) => void;
  disabled?: boolean;
}

/**
 * Component for advanced scheduling options
 * Includes auto-tuning and instructor break settings
 */
export const AdvancedOptions: React.FC<AdvancedOptionsProps> = ({
  settings,
  onChange,
  disabled = false
}) => {
  // Handle checkbox changes
  const handleChange = (field: string, checked: boolean) => {
    onChange({ [field]: checked });
  };
  
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-medium text-gray-700">Advanced Options</h3>
        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded">Optional</span>
      </div>
      
      <p className="text-sm text-gray-500 mb-4">
        These settings are for fine-tuning the scheduling process. The default values work well for most schedules.
      </p>
      
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="autoTuneWeights"
              type="checkbox"
              checked={settings.autoTuneWeights}
              onChange={(e) => handleChange('autoTuneWeights', e.target.checked)}
              disabled={disabled}
              className={`h-4 w-4 text-blue-600 rounded border-gray-300 ${disabled ? 'cursor-not-allowed' : ''}`}
            />
          </div>
          <div className="ml-3">
            <label htmlFor="autoTuneWeights" className="font-medium text-gray-700">Auto-tune weights</label>
            <p className="text-sm text-gray-500">
              Automatically adjust priorities based on schedule complexity. May override manual priority settings.
            </p>
          </div>
        </div>
        
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="requireBreakBetweenClasses"
              type="checkbox"
              checked={settings.requireBreakBetweenClasses}
              onChange={(e) => handleChange('requireBreakBetweenClasses', e.target.checked)}
              disabled={disabled}
              className={`h-4 w-4 text-blue-600 rounded border-gray-300 ${disabled ? 'cursor-not-allowed' : ''}`}
            />
          </div>
          <div className="ml-3">
            <label htmlFor="requireBreakBetweenClasses" className="font-medium text-gray-700">Required break between classes</label>
            <p className="text-sm text-gray-500">
              Ensures instructors have at least one period break between consecutive classes when possible.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
