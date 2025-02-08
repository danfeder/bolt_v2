import React, { useCallback } from 'react';
import { Upload, Info } from 'lucide-react';
import { parseClassesCSV } from '../lib/csvParser';
import { useScheduleStore } from '../store/scheduleStore';

export const FileUpload: React.FC = () => {
  const { setClasses } = useScheduleStore();

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const classes = parseClassesCSV(text);
      setClasses(classes);
    };
    reader.readAsText(file);
  }, [setClasses]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Info className="text-blue-500" />
            <h3 className="font-medium">File Format Guidelines</h3>
          </div>
          <div className="text-sm text-gray-600">
            <p><strong>Classes CSV format:</strong> Name, Conflicts</p>
            <p className="text-xs mt-1">Example: 1-409, 1-3,2-4,3-6 (conflicts on Monday period 3, Tuesday period 4, Wednesday period 6)</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg cursor-pointer hover:bg-blue-600">
            <Upload size={20} />
            <span>Upload Classes List</span>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
        </div>
      </div>
    </div>
  );
};