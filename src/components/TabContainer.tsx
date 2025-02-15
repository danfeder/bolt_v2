import { FC } from 'react';
import { useScheduleStore } from '../store/scheduleStore';
import { SchedulerTab } from '../types';
import { FileUpload } from './FileUpload';
import { ConstraintsForm } from './ConstraintsForm';
import { Calendar } from './Calendar';
import { ScheduleDebugPanel } from './ScheduleDebugPanel';
import { ClassEditor } from './ClassEditor';
import { InstructorAvailability } from './InstructorAvailability';

interface TabButtonProps {
  tab: SchedulerTab;
  currentTab: SchedulerTab;
  isValid: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

const TabButton: FC<TabButtonProps> = ({ tab, currentTab, isValid, onClick, children }) => (
  <button
    onClick={onClick}
    disabled={!isValid}
    className={`px-4 py-2 rounded-t-lg transition-colors ${
      currentTab === tab
        ? 'bg-blue-100 text-blue-800 border-b-2 border-blue-500'
        : isValid
        ? 'bg-gray-100 hover:bg-gray-200 text-gray-800'
        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
    }`}
  >
    {children}
  </button>
);

export const TabContainer: FC = () => {
  const {
    currentTab,
    setCurrentTab,
    tabValidation,
    classes,
    assignments,
    lastGenerationMetadata,
    generateSchedule,
    error,
    clearError
  } = useScheduleStore();

  const setupValid = classes.length > 0;
  const visualizeValid = setupValid && assignments.length > 0;
  const debugValid = lastGenerationMetadata !== null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-4 border-b border-gray-200">
        <div className="flex gap-2">
          <TabButton
            tab="setup"
            currentTab={currentTab}
            isValid={true} // Setup is always accessible
            onClick={() => setCurrentTab('setup')}
          >
            Setup
          </TabButton>
          <TabButton
            tab="visualize"
            currentTab={currentTab}
            isValid={visualizeValid}
            onClick={() => setCurrentTab('visualize')}
          >
            Visualize
          </TabButton>
          <TabButton
            tab="debug"
            currentTab={currentTab}
            isValid={debugValid}
            onClick={() => setCurrentTab('debug')}
          >
            Debug
          </TabButton>
        </div>
      </div>

      <div className="mt-4">
        {currentTab === 'setup' && (
          <div className="space-y-6">
            <section className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Upload Schedule Data</h2>
              <FileUpload />
            </section>
            <section className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Edit Classes</h2>
              <ClassEditor />
            </section>
            <section className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Instructor Availability</h2>
              <InstructorAvailability />
            </section>
            <section className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Configure Constraints</h2>
              <ConstraintsForm />
            </section>

            {error && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4">
                <div className="flex items-center">
                  <div className="text-red-400">!</div>
                  <p className="ml-3 text-red-700">{error}</p>
                  <button 
                    onClick={clearError}
                    className="ml-auto text-red-700 hover:text-red-900"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            <div className="flex justify-center">
              <button
                onClick={() => {
                  generateSchedule().then(() => {
                    setCurrentTab('visualize');
                  }).catch(() => {
                    // Error is handled by the store
                  });
                }}
                disabled={!classes.length}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg shadow hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Generate Rotation Schedule
              </button>
            </div>
          </div>
        )}

        {currentTab === 'visualize' && (
          <div className="bg-white p-6 rounded-lg shadow">
            <Calendar />
          </div>
        )}

        {currentTab === 'debug' && (
          <div className="bg-white p-6 rounded-lg shadow">
            <ScheduleDebugPanel />
          </div>
        )}
      </div>
    </div>
  );
};
