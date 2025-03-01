import React from 'react';
import type { SchedulerTab } from '../types';
import { useScheduleStore } from '../store/scheduleStore';
import { FileUpload } from './FileUpload';
import { Calendar } from './Calendar';
import { ScheduleDebugPanel } from './ScheduleDebugPanel';
import { SolverConfig } from './SolverConfig';
import { Dashboard } from './dashboard';

/**
 * TabContainer manages the main scheduling workflow through three tabs:
 * - Setup: Data upload and solver configuration
 * - Visualization: Schedule calendar view
 * - Debug: Debugging information and metrics
 */
export const TabContainer: React.FC = () => {
  const { 
    currentTab, 
    setCurrentTab,
    tabValidation
  } = useScheduleStore();

  const tabs: { id: SchedulerTab; label: string }[] = [
    { id: 'setup', label: 'Setup' },
    { id: 'visualize', label: 'Visualization' },
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'debug', label: 'Debug' }
  ];

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-6" aria-label="Tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              disabled={!tabValidation[tab.id] && tab.id !== 'setup'}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${currentTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : !tabValidation[tab.id] && tab.id !== 'setup'
                    ? 'border-transparent text-gray-400 cursor-not-allowed'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={currentTab === tab.id ? 'page' : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-8">
        {currentTab === 'setup' && (
          <div className="space-y-8">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium mb-4">Data Upload</h2>
              <FileUpload />
            </div>
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium mb-4">Solver Configuration</h2>
              <SolverConfig />
            </div>
          </div>
        )}

        {currentTab === 'visualize' && (
          <div className="bg-white shadow rounded-lg p-6">
            <Calendar />
          </div>
        )}

        {currentTab === 'dashboard' && (
          <div className="bg-white shadow rounded-lg p-6">
            <Dashboard />
          </div>
        )}

        {currentTab === 'debug' && (
          <div className="bg-white shadow rounded-lg p-6">
            <ScheduleDebugPanel />
          </div>
        )}
      </div>
    </div>
  );
};
