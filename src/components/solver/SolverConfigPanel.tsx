import React, { useState, useEffect } from 'react';
import { useScheduleStore } from '../../store/scheduleStore';
import type { SolverWeights, GeneticSolverConfig } from '../../types';
import { PresetSelector, PresetType, presets } from './SolverPresets';
import { WeightConfig } from './WeightConfig';
import { GeneticConfig } from './GeneticConfig';

/**
 * Deep equality comparison helper for objects
 */
const isEqual = (obj1: any, obj2: any): boolean => {
  if (obj1 === obj2) return true;
  if (!obj1 || !obj2) return false;
  
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  
  if (keys1.length !== keys2.length) return false;
  
  return keys1.every(key => {
    if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
      return isEqual(obj1[key], obj2[key]);
    }
    return obj1[key] === obj2[key];
  });
};

/**
 * Main component for managing solver configuration
 */
export const SolverConfigPanel: React.FC = () => {
  // Get state from the store using the correct property names
  const geneticConfig = useScheduleStore(state => state.geneticConfig);
  const setGeneticConfig = useScheduleStore(state => state.setGeneticConfig);
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
  
  // Update local state when genetic config changes, using deep comparison to prevent infinite loops
  useEffect(() => {
    if (geneticConfig && !isEqual(genetic, geneticConfig)) {
      setGenetic(geneticConfig);
    }
  }, [geneticConfig, genetic]); // genetic is now a dependency
  
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
      // Update genetic config in the store
      if (presets[preset].genetic) {
        setGeneticConfig({...presets[preset].genetic});
      }
      // For weights, we'll need to add a setWeights method to the store later
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
    
    // Currently weights aren't stored in the central state
    // We'll add that capability in the future
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
    setGeneticConfig(changes);
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
