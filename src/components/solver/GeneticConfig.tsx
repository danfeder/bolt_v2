import React from 'react';
import { GeneticSolverConfig } from '../../types';

interface GeneticConfigProps {
  config: GeneticSolverConfig;
  onChange: (config: Partial<GeneticSolverConfig>) => void;
  disabled?: boolean;
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

/**
 * Component for configuring genetic algorithm parameters
 */
export const GeneticConfig: React.FC<GeneticConfigProps> = ({ 
  config, 
  onChange,
  disabled = false
}) => {
  const handleToggleEnabled = () => {
    onChange({ enabled: !config.enabled });
  };

  const handleInputChange = (key: keyof Omit<GeneticSolverConfig, 'enabled'>) => 
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseFloat(e.target.value);
      onChange({ [key]: value });
    };

  return (
    <div className="mt-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-800">🧬 Genetic Algorithm</h3>
        
        <div className="flex items-center">
          <span className="mr-2 text-sm text-gray-600">
            {config.enabled ? 'Enabled' : 'Disabled'}
          </span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={config.enabled} 
              onChange={handleToggleEnabled}
              disabled={disabled}
              className="sr-only peer"
            />
            <div className={`w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full 
              peer ${config.enabled ? 'peer-checked:bg-blue-600' : ''} 
              peer-checked:after:translate-x-full after:content-[''] after:absolute 
              after:top-[2px] after:left-[2px] after:bg-white after:rounded-full 
              after:h-5 after:w-5 after:transition-all
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
            </div>
          </label>
        </div>
      </div>
      
      {config.enabled && (
        <div className="space-y-4 bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">
            Genetic algorithms can improve solution quality for complex schedules 
            but may increase generation time. Use for challenging constraints or 
            when solution quality is critical.
          </p>
          
          {parameters.map(param => (
            <div key={param.key} className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <label className="font-medium text-gray-700">{param.label}</label>
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
                  disabled={disabled}
                  className={`w-full appearance-none h-2 bg-gray-200 rounded cursor-pointer
                    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{param.description}</p>
            </div>
          ))}
        </div>
      )}
      
      {!config.enabled && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">
            Enable genetic algorithm optimization to improve solution quality for complex schedules.
          </p>
        </div>
      )}
    </div>
  );
};
