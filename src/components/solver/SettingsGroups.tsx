import React from 'react';
import type { SolverWeights } from '../../types';

export interface SettingConfig {
  key: keyof SolverWeights;
  label: string;
  description: string;
  isNegative?: boolean;
}

export interface SettingGroup {
  title: string;
  description: string;
  settings: SettingConfig[];
}

export const settingGroups: Record<string, SettingGroup> = {
  balance: {
    title: '📅 Schedule Balance',
    description: 'Control how classes are distributed',
    settings: [
      {
        key: 'distribution',
        label: 'Even Class Spread',
        description: 'Spread classes evenly throughout available times'
      },
      {
        key: 'daily_balance',
        label: 'Daily Balance',
        description: 'Balance number of classes per day'
      }
    ]
  },
  priorities: {
    title: '⚖️ Scheduling Goals',
    description: 'Set your scheduling preferences',
    settings: [
      {
        key: 'final_week_compression',
        label: 'Avoid Last-Minute',
        description: 'Prevent too many classes in final weeks'
      },
      {
        key: 'preferred_periods',
        label: 'Preferred Times',
        description: 'Priority for teacher preferred time slots'
      }
    ]
  },
  conflicts: {
    title: '🚫 Conflict Handling',
    description: 'Control how potential conflicts are handled',
    settings: [
      {
        key: 'avoid_periods',
        label: 'Avoid Conflicts',
        description: 'Strength of conflict avoidance',
        isNegative: true
      }
    ]
  },
  genetic: {
    title: '🧬 Genetic Optimization',
    description: 'Configure genetic algorithm parameters',
    settings: [
      {
        key: 'distribution',
        label: 'Population Size',
        description: 'Number of schedules in each generation'
      },
      {
        key: 'daily_balance',
        label: 'Elite Size',
        description: 'Number of best schedules to keep'
      }
    ]
  }
};

interface SettingSliderProps {
  setting: SettingConfig;
  value: number;
  onChange: (key: keyof SolverWeights, value: number) => void;
  disabled?: boolean;
}

/**
 * Component for a single setting slider
 */
export const SettingSlider: React.FC<SettingSliderProps> = ({ 
  setting, 
  value,
  onChange,
  disabled = false
}) => {
  const { key, label, description, isNegative } = setting;
  
  // Calculate appropriate min/max values based on setting type
  const min = isNegative ? -3000 : 0;
  const max = 4000;
  const step = 100;
  
  // Handle local slider change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(key, parseInt(e.target.value, 10));
  };
  
  return (
    <div className="mb-4">
      <div className="flex justify-between mb-1">
        <label htmlFor={`setting-${key}`} className="text-sm font-medium text-gray-700">
          {label}
        </label>
        <span className="text-sm text-gray-500">{value}</span>
      </div>
      
      <input
        id={`setting-${key}`}
        data-testid={`setting-${key}`}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer 
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      />
      
      <p className="text-xs text-gray-500 mt-1">{description}</p>
    </div>
  );
};

interface SettingsGroupProps {
  group: SettingGroup;
  weights: SolverWeights;
  onChange: (key: keyof SolverWeights, value: number) => void;
  disabled?: boolean;
}

/**
 * Component for a group of related settings
 */
export const SettingsGroupComponent: React.FC<SettingsGroupProps> = ({ 
  group, 
  weights,
  onChange,
  disabled = false
}) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      <h3 className="text-md font-medium text-gray-800 mb-2">{group.title}</h3>
      <p className="text-sm text-gray-600 mb-4">{group.description}</p>
      
      <div>
        {group.settings.map((setting) => (
          <SettingSlider
            key={setting.key}
            setting={setting}
            value={weights[setting.key]}
            onChange={onChange}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
};
