import React from 'react';
import type { ConstraintValidationResult } from './types';

interface ConstraintValidationResultsProps {
  validationResult?: ConstraintValidationResult | null;
}

/**
 * Component for displaying constraint validation results
 */
export const ConstraintValidationResults: React.FC<ConstraintValidationResultsProps> = ({
  validationResult
}) => {
  if (!validationResult) {
    return null;
  }

  // If validation passed, don't display anything
  if (validationResult.isValid && validationResult.messages.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className={`p-4 border-l-4 ${validationResult.isValid ? 'border-yellow-400 bg-yellow-50' : 'border-red-500 bg-red-50'} rounded-md`}>
        <div className="flex">
          <div className="flex-shrink-0">
            {validationResult.isValid ? (
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M8.485 3.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 3.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <div className="ml-3">
            <h3 className={`text-sm font-medium ${validationResult.isValid ? 'text-yellow-800' : 'text-red-800'}`}>
              {validationResult.isValid ? 'Warning' : 'Error'} - Constraint Validation
            </h3>
            <div className={`mt-2 text-sm ${validationResult.isValid ? 'text-yellow-700' : 'text-red-700'}`}>
              <ul className="list-disc pl-5 space-y-1">
                {validationResult.messages.map((message, index) => (
                  <li key={index}>{message}</li>
                ))}
              </ul>
            </div>
            
            {/* Display incompatible constraints if any */}
            {validationResult.incompatibleConstraints && validationResult.incompatibleConstraints.length > 0 && (
              <div className="mt-3">
                <h4 className="text-sm font-medium text-gray-700">Incompatible Constraints:</h4>
                <ul className="list-disc pl-5 space-y-1 mt-1 text-sm text-gray-600">
                  {validationResult.incompatibleConstraints.map((group, groupIndex) => (
                    <li key={groupIndex}>
                      {group.join(', ')}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Display missing dependencies if any */}
            {validationResult.missingDependencies && Object.keys(validationResult.missingDependencies).length > 0 && (
              <div className="mt-3">
                <h4 className="text-sm font-medium text-gray-700">Missing Dependencies:</h4>
                <ul className="list-disc pl-5 space-y-1 mt-1 text-sm text-gray-600">
                  {Object.entries(validationResult.missingDependencies).map(([constraint, dependencies], index) => (
                    <li key={index}>
                      <span className="font-medium">{constraint}</span> requires: {dependencies.join(', ')}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
