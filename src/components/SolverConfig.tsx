import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/apiClient';
import { SolverWeights, GeneticSolverConfig, SolverConfig as SolverConfigType } from '../types';
import { GeneticParameters } from './GeneticParameters';
import { useScheduleStore } from '../store/scheduleStore';
import './SolverConfig.css';

type PresetType = 'balanced' | 'strict' | 'teacher' | 'rapid' | 'custom';

interface PresetConfig {
  name: string;
  description: string;
  weights: SolverWeights;
  genetic?: GeneticSolverConfig;
}

const presets: Record<PresetType, PresetConfig> = {
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

interface SettingConfig {
  key: keyof SolverWeights;
  label: string;
  description: string;
  isNegative?: boolean;
}

interface SettingGroup {
  title: string;
  description: string;
  settings: SettingConfig[];
}

const settingGroups: Record<string, SettingGroup> = {
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

export const SolverConfig: React.FC = () => {
  const { geneticConfig, setGeneticConfig } = useScheduleStore();
  const [selectedPreset, setSelectedPreset] = useState<PresetType>('balanced');
  const [weights, setWeights] = useState<SolverWeights>(presets.balanced.weights);
  const [isSaving, setIsSaving] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showTour, setShowTour] = useState(false);
  const [currentTourStep, setCurrentTourStep] = useState(0);

  useEffect(() => {
    const hasSeenTour = localStorage.getItem('solverConfigTourSeen');
    if (!hasSeenTour) {
      setShowTour(true);
      localStorage.setItem('solverConfigTourSeen', 'true');
    }
  }, []);

  const tourSteps = [
    {
      title: 'Welcome to Schedule Settings! 👋',
      content: 'This tool helps you customize how flexible periods are scheduled. Required times are always respected.',
    },
    {
      title: 'Preset Configurations 📋',
      content: 'Start with these preset options to quickly get the type of schedule you need.',
    },
    {
      title: 'Priority Sliders 🎚️',
      content: 'Fine-tune individual settings by sliding left (lower priority) or right (higher priority).',
    },
    {
      title: 'Impact Indicators 🎯',
      content: 'Green dots mean low impact, yellow medium, and red high impact on the schedule.',
    },
  ];

  const handlePresetChange = (preset: PresetType) => {
    setSelectedPreset(preset);
    setWeights(presets[preset].weights);
    if (presets[preset].genetic) {
      setGeneticConfig(presets[preset].genetic as GeneticSolverConfig);
    }
  };

  const [lastChanged, setLastChanged] = useState<keyof SolverWeights | null>(null);

  const handleWeightChange = (key: keyof SolverWeights) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setLastChanged(key);
    setTimeout(() => setLastChanged(null), 1000);
    const value = parseInt(e.target.value);
    setWeights(prev => ({
      ...prev,
      [key]: value
    }));
    if (selectedPreset !== 'custom') {
      setSelectedPreset('custom');
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const config: SolverConfigType = {
        weights,
        genetic: geneticConfig
      };
      await apiClient.updateSolverConfig(config);
      alert('Settings saved successfully!');
    } catch (error) {
      alert('Failed to save settings');
      console.error('Error saving settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    handlePresetChange('balanced');
  };

  const getImpactLevel = (value: number) => {
    const absValue = Math.abs(value);
    const percentage = (absValue / 10000) * 100;
    return percentage > 66 ? '🔴' : percentage > 33 ? '🟡' : '🟢';
  };

  return (
    <div className="bg-white p-6 rounded-lg space-y-6">
      {showTour && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md">
            <h3 className="text-xl font-semibold mb-2">{tourSteps[currentTourStep].title}</h3>
            <p className="text-gray-600 mb-4">{tourSteps[currentTourStep].content}</p>
            <div className="flex justify-between">
              <button
                onClick={() => setShowTour(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                Skip Tour
              </button>
              <div className="flex gap-2">
                {currentTourStep > 0 && (
                  <button
                    onClick={() => setCurrentTourStep(prev => prev - 1)}
                    className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    Previous
                  </button>
                )}
                <button
                  onClick={() => {
                    if (currentTourStep === tourSteps.length - 1) {
                      setShowTour(false);
                    } else {
                      setCurrentTourStep(prev => prev + 1);
                    }
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {currentTourStep === tourSteps.length - 1 ? 'Finish' : 'Next'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">Schedule Settings</h2>
        <p className="text-gray-600">Choose a preset or customize your own settings</p>
        <div className="mt-2 space-y-2">
          <div className="p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">
            <strong>Required Times:</strong> If a class has required time slots, those will always be respected and cannot be adjusted here.
          </div>
          <div className="p-3 bg-yellow-50 text-yellow-800 rounded-lg text-sm">
            <strong>Tip:</strong> Use these settings to control how flexible time slots are scheduled. Start with a preset and adjust if needed.
          </div>
        </div>
        <button 
          onClick={() => setShowTour(true)}
          className="text-sm text-blue-600 hover:text-blue-800 mt-2"
        >
          Show Tour Guide
        </button>
      </div>

      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {Object.entries(presets).map(([key, preset]) => (
          <button
            key={key}
            onClick={() => handlePresetChange(key as PresetType)}
            className={`px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-colors ${
              selectedPreset === key
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {preset.name}
          </button>
        ))}
      </div>

      <div className="mb-6">
        <div className="text-sm text-gray-700 font-medium mb-2">
          {presets[selectedPreset].description}
        </div>
        <div className="text-xs text-gray-500">
          {selectedPreset === 'balanced' && "Recommended for most schedules"}
          {selectedPreset === 'strict' && "Best when you need very specific scheduling patterns"}
          {selectedPreset === 'teacher' && "Prioritizes teacher preferences and workload balance"}
          {selectedPreset === 'rapid' && "More flexible scheduling with fewer constraints"}
          {selectedPreset === 'custom' && "Your custom configuration"}
        </div>
      </div>

      {Object.entries(settingGroups).map(([groupKey, group]) => (
        <div key={groupKey} className="mb-8">
          <div className="mb-4">
            <h3 className="text-lg font-medium mb-1">{group.title}</h3>
            <p className="text-sm text-gray-600">{group.description}</p>
          </div>

          <div className="space-y-4">
            {group.settings.map(setting => (
              <div key={setting.key} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <label className="font-medium">
                    {setting.label}
                    <span className="ml-2">
                      {getImpactLevel(weights[setting.key])}
                    </span>
                  </label>
                  <span className="text-sm text-gray-500">{weights[setting.key]}</span>
                </div>
                <div className={`relative ${lastChanged === setting.key ? 'saving-indicator' : ''}`}>
                  <input
                    type="range"
                    min={setting.isNegative ? -10000 : 0}
                    max={10000}
                    value={weights[setting.key]}
                    onChange={handleWeightChange(setting.key)}
                    className={`w-full appearance-none h-2 rounded cursor-pointer ${setting.isNegative ? 'negative' : ''}`}
                    title={`Drag to adjust ${setting.label.toLowerCase()} priority`}
                  />
                  <div className="text-xs text-gray-500 mt-1 flex justify-between">
                    <span>{setting.isNegative ? 'Stronger' : 'Low'}</span>
                    <span>{setting.isNegative ? 'Weaker' : 'High'}</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">{setting.description}</p>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex justify-between pt-4 border-t">
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Reset to Default
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      <div className="mt-4 pt-4 border-t">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1"
        >
          {showAdvanced ? '🔼' : '🔽'} {showAdvanced ? 'Hide' : 'Show'} Advanced Settings
        </button>
        
        {showAdvanced && (
          <>
          <div className="mt-4 space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Day Usage Priority</h4>
              <input
                type="range"
                min={0}
                max={10000}
                value={weights.day_usage}
                onChange={handleWeightChange('day_usage')}
                className="w-full appearance-none h-2 rounded cursor-pointer"
              />
              <p className="text-xs text-gray-500 mt-1">
                Controls how much the scheduler tries to use all available days
              </p>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Earlier Dates Preference</h4>
              <input
                type="range"
                min={0}
                max={1000}
                value={weights.earlier_dates}
                onChange={handleWeightChange('earlier_dates')}
                className="w-full appearance-none h-2 rounded cursor-pointer"
              />
              <p className="text-xs text-gray-500 mt-1">
                Slight preference for scheduling classes earlier when possible
              </p>
            </div>

            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium">🧬 Genetic Optimization</h3>
                <div className="flex items-center">
                  <span className="mr-2 text-sm text-gray-600">Enable</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={geneticConfig.enabled}
              onChange={() => setGeneticConfig({
                ...geneticConfig,
                enabled: !geneticConfig.enabled
              })}
                    />
                    <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-focus:ring-4 peer-focus:ring-blue-300 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>

              <GeneticParameters
                config={geneticConfig}
                onChange={setGeneticConfig}
              />
            </div>
          </div>
          </>
        )}
      </div>
    </div>
  );
};
