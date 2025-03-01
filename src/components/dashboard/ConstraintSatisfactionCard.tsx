import React from 'react';
import type { ConstraintSatisfactionMetric } from '../../types/dashboard';

interface ConstraintSatisfactionCardProps {
  constraints: ConstraintSatisfactionMetric[];
}

/**
 * Component for displaying constraint satisfaction metrics
 */
export const ConstraintSatisfactionCard: React.FC<ConstraintSatisfactionCardProps> = ({ 
  constraints 
}) => {
  // Group constraints by category
  const constraintsByCategory = constraints.reduce<Record<string, ConstraintSatisfactionMetric[]>>(
    (acc, constraint) => {
      if (!acc[constraint.category]) {
        acc[constraint.category] = [];
      }
      acc[constraint.category].push(constraint);
      return acc;
    },
    {}
  );

  // Calculate overall satisfaction percentage
  const overallSatisfaction = constraints.length > 0
    ? (constraints.reduce((sum, c) => sum + c.percentage, 0) / constraints.length).toFixed(1)
    : '0.0';

  return (
    <div className="h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-800">Constraint Satisfaction</h3>
        <div className="text-sm bg-blue-50 text-blue-700 px-3 py-1 rounded-full">
          {overallSatisfaction}% Satisfied
        </div>
      </div>

      {Object.entries(constraintsByCategory).map(([category, categoryConstraints]) => (
        <div key={category} className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">{category}</h4>
          
          <div className="space-y-4">
            {categoryConstraints.map((constraint) => (
              <div key={constraint.name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">{constraint.name}</span>
                  <span className="font-medium">
                    {constraint.satisfied}/{constraint.total} ({constraint.percentage.toFixed(1)}%)
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className={`h-2.5 rounded-full ${getProgressColor(constraint.percentage)}`}
                    style={{ width: `${constraint.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {constraints.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No constraint satisfaction data available
        </div>
      )}
    </div>
  );
};

// Helper function to get color based on satisfaction percentage
function getProgressColor(percentage: number): string {
  if (percentage >= 90) return 'bg-green-500';
  if (percentage >= 75) return 'bg-green-400';
  if (percentage >= 60) return 'bg-yellow-400';
  if (percentage >= 40) return 'bg-orange-400';
  return 'bg-red-500';
}
