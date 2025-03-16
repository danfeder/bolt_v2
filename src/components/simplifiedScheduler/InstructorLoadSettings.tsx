import React from 'react';
import { InstructorLoadSettings as ILoadSettings } from './SimplifiedSchedulerPanel';

interface InstructorLoadProps {
  settings: ILoadSettings;
  onChange: (changes: Partial<ILoadSettings>) => void;
  disabled?: boolean;
}

/**
 * Component for setting instructor load constraints
 * Allows configuration of min/max classes per day and week
 */
export const InstructorLoadSettings: React.FC<InstructorLoadProps> = ({
  settings,
  onChange,
  disabled = false
}) => {
  // Handle numeric input changes
  const handleNumberChange = (field: string, value: string) => {
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue)) {
      onChange({ [field]: numValue });
    }
  };
  
  // Handle checkbox changes
  const handleCheckboxChange = (field: string, checked: boolean) => {
    onChange({ [field]: checked });
  };
  
  return (
    <div>
      <h3 className="text-lg font-medium text-gray-700 mb-2">Instructor Workload</h3>
      <p className="text-sm text-gray-500 mb-4">
        Set limits for how many classes an instructor can teach per day and per week.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Daily settings */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-700 mb-3">Daily Classes</h4>
          
          <div className="flex items-center mb-4">
            <label htmlFor="minPerDay" className="w-1/2 text-sm text-gray-600">
              Minimum per day:
            </label>
            <input
              id="minPerDay"
              type="number"
              min="0"
              max="10"
              value={settings.minPerDay}
              onChange={(e) => handleNumberChange('minPerDay', e.target.value)}
              disabled={disabled}
              className={`
                w-16 p-2 border border-gray-300 rounded-md text-center
                ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              `}
            />
          </div>
          
          <div className="flex items-center mb-4">
            <label htmlFor="maxPerDay" className="w-1/2 text-sm text-gray-600">
              Maximum per day:
            </label>
            <input
              id="maxPerDay"
              type="number"
              min="1"
              max="10"
              value={settings.maxPerDay}
              onChange={(e) => handleNumberChange('maxPerDay', e.target.value)}
              disabled={disabled}
              className={`
                w-16 p-2 border border-gray-300 rounded-md text-center
                ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              `}
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center">
              <input
                id="allowMinDayFlexibility"
                type="checkbox"
                checked={settings.allowMinFlexibility}
                onChange={(e) => handleCheckboxChange('allowMinFlexibility', e.target.checked)}
                disabled={disabled}
                className={`h-4 w-4 text-blue-600 rounded ${disabled ? 'cursor-not-allowed' : ''}`}
              />
              <label htmlFor="allowMinDayFlexibility" className="ml-2 text-sm text-gray-600">
                Allow flexibility on minimum
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="allowMaxDayFlexibility"
                type="checkbox"
                checked={settings.allowMaxFlexibility}
                onChange={(e) => handleCheckboxChange('allowMaxFlexibility', e.target.checked)}
                disabled={disabled}
                className={`h-4 w-4 text-blue-600 rounded ${disabled ? 'cursor-not-allowed' : ''}`}
              />
              <label htmlFor="allowMaxDayFlexibility" className="ml-2 text-sm text-gray-600">
                Allow slight flexibility on maximum
              </label>
            </div>
          </div>
        </div>
        
        {/* Weekly settings */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-700 mb-3">Weekly Classes</h4>
          
          <div className="flex items-center mb-4">
            <label htmlFor="minPerWeek" className="w-1/2 text-sm text-gray-600">
              Minimum per week:
            </label>
            <input
              id="minPerWeek"
              type="number"
              min="0"
              max="25"
              value={settings.minPerWeek}
              onChange={(e) => handleNumberChange('minPerWeek', e.target.value)}
              disabled={disabled}
              className={`
                w-16 p-2 border border-gray-300 rounded-md text-center
                ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              `}
            />
          </div>
          
          <div className="flex items-center mb-4">
            <label htmlFor="maxPerWeek" className="w-1/2 text-sm text-gray-600">
              Maximum per week:
            </label>
            <input
              id="maxPerWeek"
              type="number"
              min="1"
              max="25"
              value={settings.maxPerWeek}
              onChange={(e) => handleNumberChange('maxPerWeek', e.target.value)}
              disabled={disabled}
              className={`
                w-16 p-2 border border-gray-300 rounded-md text-center
                ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              `}
            />
          </div>
          
          {/* Note: Weekly flexibility uses the same settings as daily to simplify the interface */}
          <p className="text-xs text-gray-500 italic mt-2">
            Flexibility settings above apply to both daily and weekly limits.
          </p>
        </div>
      </div>
    </div>
  );
};
