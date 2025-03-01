import React from 'react';
import { TabContainer } from './components/TabContainer';
import { useScheduleStore } from './store/scheduleStore';
import { Calendar as CalendarIcon, Play } from 'lucide-react';
import { testClasses, testInstructorAvailability } from './store/testData';

function App() {
  const { setClasses, setInstructorAvailability } = useScheduleStore();

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
          </div>
        </div>
      </header>

      <main>
        <TabContainer />
      </main>
    </div>
  );
}

export default App;
