import React from 'react';
import type { SolverWeights, GeneticSolverConfig } from '../../types';

export type PresetType = 'balanced' | 'strict' | 'teacher' | 'rapid' | 'custom';

export interface PresetConfig {
  name: string;
  description: string;
  weights: SolverWeights;
  genetic?: GeneticSolverConfig;
}

export const presets: Record<PresetType, PresetConfig> = {
  balanced: {
    name: 'Balanced Schedule',
    description: 'Even distribution of classes with moderate priorities',
    weights: {
      final_week_compression: 3000,
      day_usage: 2000,
      daily_balance: 1500,
      preferred_periods: 1000,
      distribution: 1000,
      avoid_periods: -500,
      earlier_dates: 10,
    },
    genetic: {
      enabled: false,
      populationSize: 100,
      eliteSize: 2,
      mutationRate: 0.1,
      crossoverRate: 0.8,
      maxGenerations: 100
    }
  },
  strict: {
    name: 'Strict Requirements',
    description: 'Highest priority for preferred periods and scheduling rules',
    weights: {
      final_week_compression: 4000,
      day_usage: 2500,
      daily_balance: 2000,
      preferred_periods: 1500,
      distribution: 1200,
      avoid_periods: -1000,
      earlier_dates: 5,
    },
    genetic: {
      enabled: true,
      populationSize: 200,
      eliteSize: 4,
      mutationRate: 0.05,
      crossoverRate: 0.9,
      maxGenerations: 200
    }
  },
  teacher: {
    name: 'Teacher Friendly',
    description: 'Focus on teacher preferences and balanced workload',
    weights: {
      final_week_compression: 2000,
      day_usage: 1500,
      daily_balance: 2000,
      preferred_periods: 3000,
      distribution: 1500,
      avoid_periods: -2000,
      earlier_dates: 0,
    },
    genetic: {
      enabled: false,
      populationSize: 100,
      eliteSize: 2,
      mutationRate: 0.1,
      crossoverRate: 0.8,
      maxGenerations: 100
    }
  },
  rapid: {
    name: 'Flexible Schedule',
    description: 'More flexible scheduling with fewer constraints',
    weights: {
      final_week_compression: 1000,
      day_usage: 1000,
      daily_balance: 1000,
      preferred_periods: 500,
      distribution: 500,
      avoid_periods: -200,
      earlier_dates: 50,
    },
    genetic: {
      enabled: true,
      populationSize: 150,
      eliteSize: 3,
      mutationRate: 0.15,
      crossoverRate: 0.85,
      maxGenerations: 150
    }
  },
  custom: {
    name: 'Custom Settings',
    description: 'Fine-tune all settings manually',
    weights: {
      final_week_compression: 3000,
      day_usage: 2000,
      daily_balance: 1500,
      preferred_periods: 1000,
      distribution: 1000,
      avoid_periods: -500,
      earlier_dates: 10,
    },
    genetic: {
      enabled: false,
      populationSize: 100,
      eliteSize: 2,
      mutationRate: 0.1,
      crossoverRate: 0.8,
      maxGenerations: 100
    }
  }
};

interface PresetSelectorProps {
  selectedPreset: PresetType;
  onSelectPreset: (preset: PresetType) => void;
}

/**
 * Component for selecting solver configuration presets
 */
export const PresetSelector: React.FC<PresetSelectorProps> = ({ 
  selectedPreset, 
  onSelectPreset 
}) => {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-medium text-gray-800 mb-3">Configuration Presets</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {Object.entries(presets).map(([key, preset]) => (
          <div 
            key={key}
            className={`cursor-pointer p-3 rounded-lg transition-colors ${
              selectedPreset === key 
                ? 'bg-blue-100 border-2 border-blue-500' 
                : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
            }`}
            onClick={() => onSelectPreset(key as PresetType)}
          >
            <h4 className="font-medium text-gray-800">{preset.name}</h4>
            <p className="text-sm text-gray-600 mt-1">{preset.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
