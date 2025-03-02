import React from 'react';
import type { SolverWeights } from '../../types';
import { settingGroups, SettingsGroupComponent } from './SettingsGroups';

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
  return (
    <div className="mt-6">
      <h3 className="text-lg font-medium text-gray-800 mb-3">Solver Weights</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {Object.entries(settingGroups).map(([key, group]) => (
          <SettingsGroupComponent
            key={key}
            group={group}
            weights={weights}
            onChange={onChangeWeight}
            disabled={disabled}
          />
        ))}
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
