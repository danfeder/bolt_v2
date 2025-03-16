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
        
        {/* Schedule Date Options */}
        <div className="border-t border-gray-200 my-4 pt-4">
          <h4 className="font-medium text-gray-700 mb-2">Schedule Timing</h4>
          
          <div className="mb-4">
            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <p className="text-xs text-gray-500 mb-2">
              The earliest date to begin scheduling classes. Required for multi-week scheduling.
            </p>
            <input
              type="date"
              id="startDate"
              value={settings.startDate ? settings.startDate.toISOString().split('T')[0] : ''}
              onChange={(e) => {
                const date = e.target.value ? new Date(e.target.value) : undefined;
                onChange({ startDate: date });
              }}
              disabled={disabled}
              className={`mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm 
                focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm
                ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
            />
          </div>
        </div>
          
        {/* Enhanced constraint system options */}
        <div className="border-t border-gray-200 my-4 pt-4">
          <h4 className="font-medium text-gray-700 mb-2">Constraint System</h4>
          
          <div className="flex items-start mb-3">
            <div className="flex items-center h-5">
              <input
                id="strictValidation"
                type="checkbox"
                checked={settings.strictValidation}
                onChange={(e) => handleChange('strictValidation', e.target.checked)}
                disabled={disabled}
                className={`h-4 w-4 text-blue-600 rounded border-gray-300 ${disabled ? 'cursor-not-allowed' : ''}`}
              />
            </div>
            <div className="ml-3">
              <label htmlFor="strictValidation" className="font-medium text-gray-700">Strict constraint validation</label>
              <p className="text-sm text-gray-500">
                Enforces compatibility validation between constraints before scheduling.
              </p>
            </div>
          </div>
          
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="relaxIncompatibleConstraints"
                type="checkbox"
                checked={settings.relaxIncompatibleConstraints}
                onChange={(e) => handleChange('relaxIncompatibleConstraints', e.target.checked)}
                disabled={disabled || !settings.strictValidation}
                className={`h-4 w-4 text-blue-600 rounded border-gray-300 ${disabled || !settings.strictValidation ? 'cursor-not-allowed opacity-50' : ''}`}
              />
            </div>
            <div className="ml-3">
              <label 
                htmlFor="relaxIncompatibleConstraints" 
                className={`font-medium ${settings.strictValidation ? 'text-gray-700' : 'text-gray-400'}`}
              >
                Relax incompatible constraints
              </label>
              <p className={`text-sm ${settings.strictValidation ? 'text-gray-500' : 'text-gray-400'}`}>
                When enabled, automatically relaxes incompatible constraints instead of failing.
                Only applies when strict validation is enabled.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
