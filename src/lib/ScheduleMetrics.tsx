import React from 'react';
import { GeneticMetrics } from '../types';

interface GeneticMetricsViewProps {
  metrics: GeneticMetrics;
}

export const GeneticMetricsView: React.FC<GeneticMetricsViewProps> = ({ metrics }) => {
  return (
    <div className="bg-gray-50 p-4 rounded-lg space-y-3">
      <h3 className="font-medium mb-2">🧬 Genetic Algorithm Progress</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Generation</p>
          <p className="font-medium">{metrics.generation}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Best Fitness</p>
          <p className="font-medium">{metrics.bestFitness.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Population Diversity</p>
          <p className="font-medium">{(metrics.populationDiversity * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Average Fitness</p>
          <p className="font-medium">{metrics.averageFitness.toFixed(2)}</p>
        </div>
      </div>
      <div className="mt-2">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-500" 
            style={{ width: `${(metrics.generation / metrics.maxGenerations) * 100}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-500 mt-1">Progress: {Math.round((metrics.generation / metrics.maxGenerations) * 100)}%</p>
      </div>
    </div>
  );
};
