import React from 'react';
import { GeneticSolverConfig } from '../types';

/**
 * @deprecated This component has been moved to src/components/solver/GeneticConfig.tsx
 * Use the new component instead for better maintainability
 */

interface GeneticParametersProps {
  config: GeneticSolverConfig;
  onChange: (config: GeneticSolverConfig) => void;
}

interface ParameterConfig {
  key: keyof Omit<GeneticSolverConfig, 'enabled'>;
  label: string;
  description: string;
  min: number;
  max: number;
  step: number;
}

const parameters: ParameterConfig[] = [
  {
    key: 'populationSize',
    label: 'Population Size',
    description: 'Number of schedules in each generation',
    min: 50,
    max: 500,
    step: 10
  },
  {
    key: 'eliteSize',
    label: 'Elite Size',
    description: 'Number of best schedules to keep',
    min: 1,
    max: 10,
    step: 1
  },
  {
    key: 'mutationRate',
    label: 'Mutation Rate',
    description: 'Probability of random schedule changes',
    min: 0,
    max: 1,
    step: 0.01
  },
  {
    key: 'crossoverRate',
    label: 'Crossover Rate',
    description: 'Probability of combining schedules',
    min: 0,
    max: 1,
    step: 0.01
  },
  {
    key: 'maxGenerations',
    label: 'Max Generations',
    description: 'Maximum number of evolution cycles',
    min: 50,
    max: 1000,
    step: 10
  }
];

export const GeneticParameters: React.FC<GeneticParametersProps> = ({ config, onChange }) => {
  const handleInputChange = (key: keyof Omit<GeneticSolverConfig, 'enabled'>) => 
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseFloat(e.target.value);
      onChange({
        ...config,
        [key]: value
      });
    };

  if (!config.enabled) {
    return null;
  }

  return (
    <div className="space-y-4">
      {parameters.map(param => (
        <div key={param.key} className="bg-gray-50 p-4 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <label className="font-medium">{param.label}</label>
            <span className="text-sm text-gray-500">
              {config[param.key]}
            </span>
          </div>
          <div>
            <input
              type="range"
              min={param.min}
              max={param.max}
              step={param.step}
              value={config[param.key] as number}
              onChange={handleInputChange(param.key)}
              className="w-full appearance-none h-2 rounded cursor-pointer"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{param.description}</p>
        </div>
      ))}
    </div>
  );
};
