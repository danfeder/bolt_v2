import React from 'react';
import type { SolverWeights } from '../../types';
import { SettingsGroupComponent, SettingGroup } from './SettingsGroups';

// Define the weight settings for each group
const balanceSettings = ['distribution', 'daily_balance', 'day_usage'];
const preferenceSettings = ['preferred_periods', 'avoid_periods', 'earlier_dates', 'final_week_compression'];

// User-friendly labels for weight settings
const weightLabels: Record<keyof SolverWeights, string> = {
  distribution: 'Even Class Spread',
  daily_balance: 'Daily Balance',
  day_usage: 'Day Utilization',
  preferred_periods: 'Preferred Times',
  avoid_periods: 'Avoid Conflicts',
  earlier_dates: 'Prefer Earlier Dates',
  final_week_compression: 'Final Week Compression'
};

// Descriptions for weight settings
const weightDescriptions: Record<keyof SolverWeights, string> = {
  distribution: 'Spread classes evenly throughout available times',
  daily_balance: 'Balance number of classes per day',
  day_usage: 'Ensure days are used efficiently',
  preferred_periods: 'Prioritize preferred time periods',
  avoid_periods: 'Avoid scheduling in undesirable periods',
  earlier_dates: 'Schedule classes earlier in the term when possible',
  final_week_compression: 'Reduce the number of classes in the final week'
};

interface WeightConfigProps {
  weights: SolverWeights;
  onChangeWeight: (key: keyof SolverWeights, value: number) => void;
  disabled?: boolean;
}

/**
 * Component for configuring solver weights
 */
export const WeightConfig: React.FC<WeightConfigProps> = ({ 
  weights, 
  onChangeWeight,
  disabled = false
}) => {
  // Render slider for an individual weight setting
  const renderWeightSlider = (key: keyof SolverWeights) => {
    const isNegativeWeight = key === 'avoid_periods';
    const min = isNegativeWeight ? -2000 : 0;
    const max = 4000;
    const step = 100;

    return (
      <div className="mb-4" key={key}>
        <div className="flex justify-between mb-1">
          <label htmlFor={`setting-${key}`} className="text-sm font-medium text-gray-700">
            {weightLabels[key]}
          </label>
          <span className="text-sm text-gray-500">{weights[key]}</span>
        </div>
        <input
          id={`setting-${key}`}
          data-testid={`setting-${key}`}
          type="range"
          min={min}
          max={max}
          step={step}
          value={weights[key]}
          onChange={(e) => onChangeWeight(key, parseInt(e.target.value))}
          disabled={disabled}
          className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer 
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        />
        <p className="text-xs text-gray-500 mt-1">{weightDescriptions[key]}</p>
      </div>
    );
  };

  // Create setting groups for our component
  const balanceGroup: SettingGroup = {
    title: '📅 Schedule Balance',
    description: 'Control how classes are distributed',
    settings: balanceSettings.map(key => ({
      key: key as keyof SolverWeights,
      label: weightLabels[key as keyof SolverWeights],
      description: weightDescriptions[key as keyof SolverWeights]
    }))
  };
  
  const preferencesGroup: SettingGroup = {
    title: '🎯 Preferences & Constraints',
    description: 'Prioritize time preferences and special requirements',
    settings: preferenceSettings.map(key => ({
      key: key as keyof SolverWeights,
      label: weightLabels[key as keyof SolverWeights],
      description: weightDescriptions[key as keyof SolverWeights],
      isNegative: key === 'avoid_periods'
    }))
  };

  return (
    <div className="mt-6">
      <h3 className="text-lg font-medium text-gray-800 mb-3">Solver Weights</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SettingsGroupComponent 
          group={balanceGroup}
          weights={weights}
          onChange={onChangeWeight}
          disabled={disabled}
        />
        
        <SettingsGroupComponent 
          group={preferencesGroup}
          weights={weights}
          onChange={onChangeWeight}
          disabled={disabled}
        />
      </div>
      
      <div className="mt-4 p-3 bg-blue-50 rounded-md">
        <h4 className="text-sm font-medium text-blue-700">Understanding Weights</h4>
        <p className="text-xs text-blue-600 mt-1">
          Higher values give more importance to that aspect of scheduling.
          Negative values indicate penalties to avoid certain situations.
          Balanced configurations work best for most scenarios.
        </p>
      </div>
    </div>
  );
};
