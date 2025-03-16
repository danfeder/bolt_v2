import React from 'react';
import { PlusCircle, Trash2, Save, Clock } from 'lucide-react';
import { useScheduleStore } from '../store/scheduleStore';
import type { Class, ConflictPeriod, TimeSlot } from '../types';

// Extended version of Class with editor-specific properties
interface EditableClass extends Class {
  id: string;
  weeklySchedule?: {
    conflicts: ConflictPeriod[];
    preferredPeriods: ConflictPeriod[];
    requiredPeriods: ConflictPeriod[];
    avoidPeriods: ConflictPeriod[];
  };
}

const PERIODS = Array.from({ length: 8 }, (_, i) => i + 1);
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const GRADES = ['Pre-K', 'K', '1', '2', '3', '4', '5', 'multiple'];

type CellState = 'blank' | 'conflict' | 'preferred' | 'required' | 'avoid';

export const ClassEditor: React.FC = () => {
  const { classes: storeClasses, setClasses } = useScheduleStore();
  const [editableClasses, setEditableClasses] = React.useState<EditableClass[]>([]);
  const [selectedClassId, setSelectedClassId] = React.useState<string>('');
  const [editedClass, setEditedClass] = React.useState<EditableClass | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);
  const [selectedGrade, setSelectedGrade] = React.useState<string>('Pre-K');
  const [gradeLunchPeriod, setGradeLunchPeriod] = React.useState<number>(0);

  // Convert store classes to editable classes with IDs and weekly schedule
  React.useEffect(() => {
    const converted = storeClasses.map((c, index) => {
      // Create an ID if not already present in our editable classes
      const existingClass = editableClasses.find(ec => ec.name === c.name && ec.grade === c.grade);
      // Ensure stable IDs by using consistent identifiers
      const id = existingClass?.id || `class-${c.name}-${c.grade}-${index}`;
      
      // Convert from the API Class format to our editable format
      return {
        ...c,
        id,
        weeklySchedule: {
          conflicts: c.conflicts || [],
          preferredPeriods: [],
          requiredPeriods: c.conflicts?.map(conflict => ({
            dayOfWeek: conflict.dayOfWeek,
            period: conflict.period
          })) || [],
          avoidPeriods: []
        }
      };
    });
    
    setEditableClasses(converted);
    
    // Select the first class if none is selected
    if (converted.length > 0 && !selectedClassId) {
      setSelectedClassId(converted[0].id);
    }
  }, [storeClasses]);

  React.useEffect(() => {
    const classToEdit = editableClasses.find(c => c.id === selectedClassId);
    if (classToEdit) {
      setEditedClass({ ...classToEdit });
    } else {
      setEditedClass(null);
    }
    setHasUnsavedChanges(false);
  }, [selectedClassId, editableClasses]);

  const addClass = () => {
    const newClass: EditableClass = {
      id: `class-${Date.now()}`,
      name: '',
      grade: 'Pre-K',
      conflicts: [],
      required_periods: [],
      weeklySchedule: {
        conflicts: [],
        preferredPeriods: [],
        requiredPeriods: [],
        avoidPeriods: []
      }
    };
    const newEditableClasses = [...editableClasses, newClass];
    setEditableClasses(newEditableClasses);
    
    // Update the store classes
    const storeClass: Class = {
      name: newClass.name,
      grade: newClass.grade,
      conflicts: newClass.conflicts,
      required_periods: newClass.required_periods
    };
    setClasses([...storeClasses, storeClass]);
    
    setSelectedClassId(newClass.id);
  };

  const removeClass = () => {
    if (!selectedClassId || !editedClass) return;
    
    // Remove from editable classes
    const newEditableClasses = editableClasses.filter(c => c.id !== selectedClassId);
    setEditableClasses(newEditableClasses);
    
    // Remove from store classes
    const newStoreClasses = storeClasses.filter(c => c.name !== editedClass.name || c.grade !== editedClass.grade);
    setClasses(newStoreClasses);
    
    setSelectedClassId(newEditableClasses[0]?.id || '');
  };

  const updateEditedClass = (updates: Partial<EditableClass>) => {
    if (!editedClass) return;
    setEditedClass({ ...editedClass, ...updates });
    setHasUnsavedChanges(true);
  };

  const saveChanges = () => {
    if (!editedClass) return;
    
    // Update editable classes
    const newEditableClasses = editableClasses.map(c => 
      c.id === editedClass.id ? editedClass : c
    );
    setEditableClasses(newEditableClasses);
    
    // Update store classes
    const updatedStoreClasses = storeClasses.map(c => {
      if (c.name === editedClass.name || (editedClass.weeklySchedule && c.name === '')) {
        // Create a store-compatible class object
        return {
          name: editedClass.name,
          grade: editedClass.grade,
          conflicts: editedClass.weeklySchedule?.conflicts || [],
          required_periods: editedClass.required_periods || []
        };
      }
      return c;
    });
    setClasses(updatedStoreClasses);
    
    setHasUnsavedChanges(false);
  };

  const getCellState = (day: number, period: number): CellState => {
    if (!editedClass || !editedClass.weeklySchedule) return 'blank';
    
    const isConflict = editedClass.weeklySchedule.conflicts.some(
      (c: ConflictPeriod) => c.dayOfWeek === day && c.period === period
    );
    
    const isRequired = editedClass.weeklySchedule.requiredPeriods.some(
      (r: ConflictPeriod) => r.dayOfWeek === day && r.period === period
    );
    
    const isPreferred = editedClass.weeklySchedule.preferredPeriods.some(
      (p: ConflictPeriod) => p.dayOfWeek === day && p.period === period
    );

    const isAvoid = editedClass.weeklySchedule.avoidPeriods.some(
      (a: ConflictPeriod) => a.dayOfWeek === day && a.period === period
    );
    
    if (isConflict) return 'conflict';
    if (isRequired) return 'required';
    if (isPreferred) return 'preferred';
    if (isAvoid) return 'avoid';
    return 'blank';
  };

  const toggleCellState = (day: number, period: number) => {
    if (!editedClass || !editedClass.weeklySchedule) return;

    const currentState = getCellState(day, period);
    const timeSlot: TimeSlot = { dayOfWeek: day, period };

    let newConflicts = [...(editedClass.weeklySchedule?.conflicts || [])];
    let newPreferred = [...(editedClass.weeklySchedule?.preferredPeriods || [])];
    let newRequired = [...(editedClass.weeklySchedule?.requiredPeriods || [])];
    let newAvoid = [...(editedClass.weeklySchedule?.avoidPeriods || [])];

    switch (currentState) {
      case 'blank':
        // Blank → Conflict
        newConflicts = [...newConflicts, timeSlot];
        break;
      case 'conflict':
        // Conflict → Preferred
        newConflicts = newConflicts.filter(
          (c: ConflictPeriod) => !(c.dayOfWeek === day && c.period === period)
        );
        newPreferred = [...newPreferred, timeSlot];
        break;
      case 'preferred':
        // Preferred → Required
        newPreferred = newPreferred.filter(
          (p: ConflictPeriod) => !(p.dayOfWeek === day && p.period === period)
        );
        newRequired = [...newRequired, timeSlot];
        break;
      case 'required':
        // Required → Avoid
        newRequired = newRequired.filter(
          (r: ConflictPeriod) => !(r.dayOfWeek === day && r.period === period)
        );
        newAvoid = [...newAvoid, timeSlot];
        break;
      case 'avoid':
        // Avoid → Blank
        newAvoid = newAvoid.filter(
          (a: ConflictPeriod) => !(a.dayOfWeek === day && a.period === period)
        );
        break;
    }

    updateEditedClass({
      weeklySchedule: {
        conflicts: newConflicts,
        preferredPeriods: newPreferred,
        requiredPeriods: newRequired,
        avoidPeriods: newAvoid
      }
    });
  };

  const setGradeLunch = () => {
    if (!gradeLunchPeriod) return;

    const updatedClasses = editableClasses.map((classObj: EditableClass) => {
      if (classObj.grade !== selectedGrade || !classObj.weeklySchedule) return classObj;

      const nonLunchConflicts = classObj.weeklySchedule.conflicts.filter(
        (conflict: ConflictPeriod) => !DAYS.some((_, idx) => 
          conflict.dayOfWeek === idx + 1 && conflict.period === gradeLunchPeriod
        )
      );

      const lunchConflicts = DAYS.map((_, idx) => ({
        dayOfWeek: idx + 1,
        period: gradeLunchPeriod
      }));

      return {
        ...classObj,
        weeklySchedule: {
          ...classObj.weeklySchedule,
          conflicts: [...nonLunchConflicts, ...lunchConflicts]
        }
      };
    });

    // Update editable classes
    setEditableClasses(updatedClasses);
    
    // Convert to store classes and update
    const storeClassesUpdate = updatedClasses.map((c: EditableClass): Class => ({
      name: c.name,
      grade: c.grade,
      conflicts: c.weeklySchedule?.conflicts || [],
      required_periods: c.required_periods || []
    }));
    setClasses(storeClassesUpdate);
    
    // Update edited class if affected
    if (editedClass?.grade === selectedGrade) {
      const updatedClass = updatedClasses.find(c => c.id === editedClass.id);
      if (updatedClass) setEditedClass(updatedClass);
    }
  };

  if (editableClasses.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md text-center">
        <p className="text-gray-500 mb-4">No classes available. Add a class or import from CSV.</p>
        <button
          onClick={addClass}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 mx-auto"
        >
          <PlusCircle size={20} />
          Add Class
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Class Editor</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={addClass}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            <PlusCircle size={20} />
            Add Class
          </button>
        </div>
      </div>

      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock size={20} className="text-blue-500" />
          Set Grade Lunch Periods
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Grade
              <select
                value={selectedGrade}
                onChange={(e) => setSelectedGrade(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                {GRADES.map(grade => (
                  <option key={grade} value={grade}>{grade}</option>
                ))}
              </select>
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Lunch Period
              <select
                value={gradeLunchPeriod}
                onChange={(e) => setGradeLunchPeriod(Number(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option key="select-period-0" value={0}>Select period</option>
                {PERIODS.map(period => (
                  <option key={`period-${period}`} value={period}>{period}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex items-end">
            <button
              onClick={setGradeLunch}
              disabled={!gradeLunchPeriod}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Set Lunch Period
            </button>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          This will set the lunch period for all classes in the selected grade. For "multiple" grade classes, set lunch periods individually.
        </p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Class
          <select
            value={selectedClassId}
            onChange={(e) => setSelectedClassId(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            {editableClasses.map((c, index) => (
              <option key={c.id || `temp-class-${index}`} value={c.id}>{c.name || 'Unnamed Class'}</option>
            ))}
          </select>
        </label>
      </div>

      {editedClass && (
        <div className="border rounded-lg p-4">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Class Name
                  <input
                    type="text"
                    value={editedClass.name}
                    onChange={(e) => updateEditedClass({ name: e.target.value })}
                    placeholder="e.g., 1-409"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Grade Level
                  <select
                    value={editedClass.grade}
                    onChange={(e) => updateEditedClass({ grade: e.target.value })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    {GRADES.map(grade => (
                      <option key={`grade-${grade}`} value={grade}>{grade}</option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={saveChanges}
                disabled={!hasUnsavedChanges}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                  hasUnsavedChanges
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
                title={hasUnsavedChanges ? 'Save changes' : 'No changes to save'}
              >
                <Save size={20} />
                Save
              </button>
              <button
                onClick={removeClass}
                className="p-2 text-red-500 hover:text-red-600"
                title="Remove class"
              >
                <Trash2 size={20} />
              </button>
            </div>
          </div>

          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Schedule Grid</h3>
            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <p className="text-sm text-gray-600">
                Click cells to toggle between states:
                <span className="inline-flex items-center gap-2 ml-2">
                  <span className="w-4 h-4 bg-gray-50 rounded"></span> Available
                  <span className="w-4 h-4 bg-red-100 rounded"></span> Conflict
                  <span className="w-4 h-4 bg-green-100 rounded"></span> Preferred
                  <span className="w-4 h-4 bg-amber-200 rounded"></span> Required
                  <span className="w-4 h-4 bg-purple-100 rounded"></span> Avoid
                </span>
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-200">
                <thead>
                  <tr>
                    <th className="border p-2">Period</th>
                    {DAYS.map((day, index) => (
                      <th key={`day-${index}-${day}`} className="border p-2">{day}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {PERIODS.map(period => (
                    <tr key={`period-row-${period}`}>
                      <td className="border p-2 font-medium">{period}</td>
                      {DAYS.map((_, dayIndex) => {
                        const state = getCellState(dayIndex + 1, period);
                        return (
                          <td
                            key={`cell-${dayIndex}-${period}`}
                            className="border p-2"
                            onClick={() => toggleCellState(dayIndex + 1, period)}
                          >
                            <div
                              className={`w-full h-8 rounded cursor-pointer transition-colors ${
                                state === 'conflict'
                                  ? 'bg-red-100 hover:bg-red-200'
                                  : state === 'preferred'
                                  ? 'bg-green-100 hover:bg-green-200'
                                  : state === 'required'
                                  ? 'bg-amber-200 hover:bg-amber-300'
                                  : state === 'avoid'
                                  ? 'bg-purple-100 hover:bg-purple-200'
                                  : 'bg-gray-50 hover:bg-gray-100'
                              }`}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};