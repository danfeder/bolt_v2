import React, { useState, useEffect } from 'react';
import { apiClient } from '../../lib/apiClient';
import type { ConstraintMetadata } from '../../types';

interface ConstraintInfoProps {
  constraintName: string;
  onClose: () => void;
}

/**
 * Component for displaying detailed information about a specific constraint
 */
export const ConstraintInfo: React.FC<ConstraintInfoProps> = ({
  constraintName,
  onClose
}) => {
  const [constraint, setConstraint] = useState<ConstraintMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch constraint details on mount
  useEffect(() => {
    const fetchConstraintInfo = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getConstraintInfo(constraintName);
        setConstraint(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch constraint information');
        console.error('Error fetching constraint info:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchConstraintInfo();
  }, [constraintName]);
  
  if (loading) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Loading constraint information...</h2>
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4 py-1">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
          <h2 className="text-lg font-medium text-red-600 mb-4">Error</h2>
          <p className="text-gray-700 mb-6">{error}</p>
          <div className="flex justify-end">
            <button
              type="button"
              className="inline-flex justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500"
              onClick={onClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  if (!constraint) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full">
        <h2 className="text-lg font-medium text-gray-900 mb-2">{constraint.name}</h2>
        <p className="text-sm text-gray-500 mb-4">Category: {constraint.category}</p>
        
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700">Description</h3>
          <p className="text-sm text-gray-600 mt-1">{constraint.description}</p>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-medium text-gray-700">Default Enabled</h3>
            <p className="text-sm text-gray-600 mt-1">
              {constraint.default_enabled ? 'Yes' : 'No'}
            </p>
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-700">Relaxable</h3>
            <p className="text-sm text-gray-600 mt-1">
              {constraint.is_relaxable ? 'Yes' : 'No'}
            </p>
          </div>
          
          {constraint.default_weight !== null && (
            <div>
              <h3 className="text-sm font-medium text-gray-700">Default Weight</h3>
              <p className="text-sm text-gray-600 mt-1">{constraint.default_weight}</p>
            </div>
          )}
        </div>
        
        {constraint.incompatible_with && constraint.incompatible_with.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-700">Incompatible With</h3>
            <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
              {constraint.incompatible_with.map((name, index) => (
                <li key={index}>{name}</li>
              ))}
            </ul>
          </div>
        )}
        
        {constraint.requires && constraint.requires.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-700">Required Dependencies</h3>
            <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
              {constraint.requires.map((name, index) => (
                <li key={index}>{name}</li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="flex justify-end">
          <button
            type="button"
            className="inline-flex justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-500"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
