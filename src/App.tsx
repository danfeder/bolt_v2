import React from 'react';
import { Calendar } from './components/Calendar';
import { FileUpload } from './components/FileUpload';
import { InstructorAvailability } from './components/InstructorAvailability';
import { ConstraintsForm } from './components/ConstraintsForm';
import { ClassEditor } from './components/ClassEditor';
import { ScheduleDebugPanel } from './components/ScheduleDebugPanel';
import { SolverConfig } from './components/SolverConfig';
import { useScheduleStore } from './store/scheduleStore';
import { Calendar as CalendarIcon, AlertCircle, Play, Settings } from 'lucide-react';
import { testClasses, testInstructorAvailability } from './store/testData';

function App() {
  const { classes, generateSchedule, setClasses, setInstructorAvailability } = useScheduleStore();
  const [error, setError] = React.useState<string | null>(null);
  const [showConfig, setShowConfig] = React.useState(false);

  const handleGenerateSchedule = () => {
    try {
      setError(null);
      generateSchedule();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const loadTestData = () => {
    setClasses(testClasses);
    setInstructorAvailability(testInstructorAvailability);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CalendarIcon className="text-blue-500" />
            <h1 className="text-3xl font-bold text-gray-900">Gym Class Rotation Scheduler</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadTestData}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              <Play size={20} />
              Load Test Data
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              <Settings size={20} />
              {showConfig ? 'Hide Config' : 'Show Config'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <FileUpload />
          </div>

          <ClassEditor />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <InstructorAvailability />
            <ConstraintsForm />
          </div>

          {showConfig && (
            <div className="bg-white shadow rounded-lg">
              <SolverConfig />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex items-center">
                <AlertCircle className="text-red-400" />
                <p className="ml-3 text-red-700">{error}</p>
              </div>
            </div>
          )}

          <div className="flex justify-center">
            <button
              onClick={handleGenerateSchedule}
              disabled={classes.length === 0}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg shadow hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Generate Rotation Schedule
            </button>
          </div>

          <Calendar />
        </div>
      </main>

      <ScheduleDebugPanel />
    </div>
  );
}

export default App;
