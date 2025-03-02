import React, { useState, useEffect } from 'react';
import { useScheduleStore } from '../../store/scheduleStore';
import type { SolverWeights, GeneticSolverConfig } from '../../types';
import { PresetSelector, PresetType, presets } from './SolverPresets';
import { WeightConfig } from './WeightConfig';
import { GeneticConfig } from './GeneticConfig';

/**
 * Main component for managing solver configuration
 */
export const SolverConfigPanel: React.FC = () => {
  const solverConfig = useScheduleStore(state => state.solverConfig);
  const setSolverConfig = useScheduleStore(state => state.setSolverConfig);
  const isGenerating = useScheduleStore(state => state.isGenerating);
  
  const [selectedPreset, setSelectedPreset] = useState<PresetType>('balanced');
  const [weights, setWeights] = useState<SolverWeights>(presets.balanced.weights);
  const [genetic, setGenetic] = useState<GeneticSolverConfig>(
    presets.balanced.genetic || {
      enabled: false,
      populationSize: 100,
      eliteSize: 2,
      mutationRate: 0.1,
      crossoverRate: 0.8,
      maxGenerations: 100
    }
  );
  
  // Update local state when solver config changes
  useEffect(() => {
    if (solverConfig) {
      setWeights(solverConfig.weights);
      if (solverConfig.genetic) {
        setGenetic(solverConfig.genetic);
      }
    }
  }, [solverConfig]);
  
  // Handle preset selection
  const handleSelectPreset = (preset: PresetType) => {
    setSelectedPreset(preset);
    setWeights({...presets[preset].weights});
    
    // Only update genetic if it exists in the preset
    if (presets[preset].genetic) {
      setGenetic({...presets[preset].genetic!});
    }
    
    // If not custom preset, also update the store
    if (preset !== 'custom') {
      setSolverConfig({
        weights: {...presets[preset].weights},
        genetic: presets[preset].genetic ? {...presets[preset].genetic} : undefined
      });
    }
  };
  
  // Handle weight changes
  const handleWeightChange = (key: keyof SolverWeights, value: number) => {
    const newWeights = { ...weights, [key]: value };
    setWeights(newWeights);
    
    // Move to custom preset when manually changing values
    if (selectedPreset !== 'custom') {
      setSelectedPreset('custom');
    }
    
    // Update the store
    setSolverConfig({
      weights: newWeights,
      genetic
    });
  };
  
  // Handle genetic config changes
  const handleGeneticChange = (changes: Partial<GeneticSolverConfig>) => {
    const newGenetic = { ...genetic, ...changes };
    setGenetic(newGenetic);
    
    // Move to custom preset when manually changing values
    if (selectedPreset !== 'custom') {
      setSelectedPreset('custom');
    }
    
    // Update the store
    setSolverConfig({
      weights,
      genetic: newGenetic
    });
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Solver Configuration</h2>
      
      <PresetSelector 
        selectedPreset={selectedPreset} 
        onSelectPreset={handleSelectPreset} 
      />
      
      <div className="border-t border-gray-200 my-6 pt-6">
        <WeightConfig 
          weights={weights}
          onChangeWeight={handleWeightChange}
          disabled={isGenerating}
        />
      </div>
      
      <div className="border-t border-gray-200 my-6 pt-6">
        <GeneticConfig 
          config={genetic}
          onChange={handleGeneticChange}
          disabled={isGenerating}
        />
      </div>
      
      {isGenerating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-blue-700">
            Configuration is locked while generating a schedule. Please wait for the 
            current operation to complete.
          </p>
        </div>
      )}
    </div>
  );
};
