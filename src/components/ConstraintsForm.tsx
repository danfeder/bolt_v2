import React from 'react';
import { Settings, Loader2 } from 'lucide-react';
import { useScheduleStore } from '../store/scheduleStore';
import { format, parseISO } from 'date-fns';

export const ConstraintsForm: React.FC = () => {
  const { constraints, setConstraints, isGenerating, generationProgress } = useScheduleStore();

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    
    if (type === 'date') {
      const date = new Date(`${value}T00:00:00`);
      if (!isNaN(date.getTime())) {
        setConstraints({
          [name]: date.toISOString()
        });
      }
    } else if (name === 'maxConsecutiveClasses') {
      setConstraints({
        [name]: parseInt(value, 10) as 1 | 2
      });
    } else if (name === 'consecutiveClassesRule') {
      setConstraints({
        [name]: value as 'hard' | 'soft'
      });
    } else {
      const numValue = parseInt(value, 10);
      if (!isNaN(numValue)) {
        setConstraints({
          [name]: numValue
        });
      }
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = parseISO(dateString);
      if (isNaN(date.getTime())) {
        return format(new Date(), 'yyyy-MM-dd');
      }
      return format(date, 'yyyy-MM-dd');
    } catch {
      return format(new Date(), 'yyyy-MM-dd');
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="text-blue-500" />
        <h2 className="text-xl font-semibold">Schedule Constraints</h2>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Start Date
              <input
                type="date"
                name="startDate"
                value={formatDate(constraints.startDate)}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
            <p className="mt-1 text-sm text-gray-500">
              When should the rotation schedule begin?
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              End Date
              <input
                type="date"
                name="endDate"
                value={formatDate(constraints.endDate)}
                onChange={handleChange}
                min={formatDate(constraints.startDate)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
            <p className="mt-1 text-sm text-gray-500">
              When should the rotation schedule end?
            </p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Maximum Classes Per Day
            <input
              type="number"
              name="maxClassesPerDay"
              value={constraints.maxClassesPerDay}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              min="1"
              max="8"
            />
          </label>
          <p className="mt-1 text-sm text-gray-500">
            Maximum number of classes that can be scheduled in a single day
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Maximum Classes Per Week
              <input
                type="number"
                name="maxClassesPerWeek"
                value={constraints.maxClassesPerWeek}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                min="1"
                max="40"
              />
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Maximum number of classes that can be scheduled in a week
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Classes Per Week
              <input
                type="number"
                name="minPeriodsPerWeek"
                value={constraints.minPeriodsPerWeek}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                min="1"
                max={constraints.maxClassesPerWeek}
              />
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Minimum number of classes that must be scheduled each week (pro-rated for partial weeks)
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Maximum Consecutive Classes
              <select
                name="maxConsecutiveClasses"
                value={constraints.maxConsecutiveClasses}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value={1}>1 class</option>
                <option value={2}>2 classes</option>
              </select>
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Maximum number of classes that can be scheduled consecutively
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Consecutive Classes Rule
              <select
                name="consecutiveClassesRule"
                value={constraints.consecutiveClassesRule}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="hard">Hard constraint (strictly enforced)</option>
                <option value="soft">Soft constraint (preferred but not required)</option>
              </select>
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Determines whether the consecutive classes limit is strictly enforced or just preferred
            </p>
          </div>
        </div>
      </div>

      {isGenerating && (
        <div className="mt-6 bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Loader2 className="animate-spin text-blue-500" />
            <span className="font-medium">Generating Schedule...</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-500 h-2.5 rounded-full transition-all duration-300" 
              style={{ width: `${generationProgress}%` }}
            />
          </div>
          <p className="mt-2 text-sm text-gray-600">
            This may take a few moments. The schedule is being optimized to meet all constraints.
          </p>
        </div>
      )}
    </div>
  );
};