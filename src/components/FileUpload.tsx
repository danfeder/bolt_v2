import React, { useCallback, useState } from 'react';
import { Upload, Info, File, X, CheckCircle, AlertTriangle } from 'lucide-react';
import { parseClassesCSV } from '../lib/csvParser';
import { useScheduleStore } from '../store/scheduleStore';
import type { Class } from '../types';

/**
 * Interface for the drag-and-drop zone component
 */
interface DropZoneProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
}

/**
 * Component for drag-and-drop file upload
 */
const DropZone: React.FC<DropZoneProps> = ({ onFileSelect, isUploading }) => {
  const [isDragging, setIsDragging] = useState(false);
  
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        onFileSelect(file);
      }
    }
  }, [onFileSelect]);
  
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  }, [onFileSelect]);
  
  return (
    <div 
      className={`border-2 border-dashed rounded-lg p-6 transition-colors text-center
        ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        ${isUploading ? 'bg-gray-50 opacity-75' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex flex-col items-center justify-center gap-3">
        <Upload className={isDragging ? 'text-blue-500' : 'text-gray-400'} size={32} />
        
        <div className="text-sm text-gray-600">
          <p className="font-medium">
            {isDragging ? 'Drop your CSV file here' : 'Drag & drop your CSV file, or'}
          </p>
          <label className="mt-2 inline-block px-4 py-2 bg-blue-500 text-white rounded-lg cursor-pointer hover:bg-blue-600">
            <span>Browse Files</span>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
          </label>
        </div>
      </div>
    </div>
  );
};

/**
 * Interface for the file info component
 */
interface FileInfoProps {
  file: File;
  onRemove: () => void;
  validationStatus?: 'valid' | 'invalid' | 'loading';
  validationMessage?: string;
}

/**
 * Component for displaying uploaded file information
 */
const FileInfo: React.FC<FileInfoProps> = ({ 
  file, 
  onRemove, 
  validationStatus = 'loading',
  validationMessage
}) => {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <File className="text-blue-500" size={24} />
      
      <div className="flex-1 overflow-hidden">
        <p className="font-medium text-gray-800 text-sm truncate">{file.name}</p>
        <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(0)} KB</p>
      </div>
      
      <div className="flex items-center gap-2">
        {validationStatus === 'loading' && (
          <div className="animate-pulse w-5 h-5 bg-blue-200 rounded-full"></div>
        )}
        
        {validationStatus === 'valid' && (
          <CheckCircle className="text-green-500" size={20} />
        )}
        
        {validationStatus === 'invalid' && (
          <AlertTriangle className="text-red-500" size={20} />
        )}
        
        <button 
          onClick={onRemove}
          className="p-1 text-gray-400 hover:text-red-500 rounded-full hover:bg-gray-100"
          aria-label="remove file"
        >
          <X size={18} />
        </button>
      </div>
      
      {validationMessage && validationStatus === 'invalid' && (
        <div className="text-red-500 text-xs mt-1 w-full">
          {validationMessage}
        </div>
      )}
    </div>
  );
};

/**
 * Interface for the data preview component
 */
interface ClassPreviewProps {
  classes: Class[];
  onImport: () => void;
  isLoading: boolean;
}

/**
 * Component for previewing parsed class data
 */
const ClassPreview: React.FC<ClassPreviewProps> = ({ classes, onImport, isLoading }) => {
  if (classes.length === 0) {
    return null;
  }
  
  return (
    <div className="mt-4 border rounded-lg overflow-hidden">
      <div className="bg-gray-50 p-3 border-b flex justify-between items-center">
        <h3 className="font-medium text-gray-800">Preview ({classes.length} classes)</h3>
        <button
          onClick={onImport}
          disabled={isLoading}
          className={`px-4 py-1 rounded-lg text-white text-sm ${
            isLoading ? 'bg-gray-400' : 'bg-green-500 hover:bg-green-600'
          }`}
        >
          {isLoading ? 'Importing...' : 'Import Classes'}
        </button>
      </div>
      
      <div className="overflow-x-auto max-h-64 overflow-y-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Conflicts</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Required</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {classes.slice(0, 5).map((cls, index) => (
              <tr key={index}>
                <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-800">{cls.name}</td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{cls.grade}</td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                  {cls.conflicts.length}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                  {cls.required_periods.length}
                </td>
              </tr>
            ))}
            {classes.length > 5 && (
              <tr>
                <td colSpan={4} className="px-3 py-2 text-sm text-gray-500 text-center">
                  ...and {classes.length - 5} more
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

/**
 * Interface for the template download component
 */
interface TemplateDownloadProps {
  onDownload: () => void;
}

/**
 * Component for downloading CSV templates
 */
const TemplateDownload: React.FC<TemplateDownloadProps> = ({ onDownload }) => {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mt-4">
      <div className="flex items-center gap-2">
        <Info className="text-blue-500" size={18} />
        <span className="text-sm font-medium text-gray-700">File Format Guidelines</span>
      </div>
      <button
        onClick={onDownload}
        className="text-sm text-blue-500 hover:text-blue-700"
      >
        Download CSV Template
      </button>
    </div>
  );
};

/**
 * Main FileUpload component
 */
export const FileUpload: React.FC = () => {
  const setClasses = useScheduleStore(state => state.setClasses);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [parsedClasses, setParsedClasses] = useState<Class[]>([]);
  const [validationStatus, setValidationStatus] = useState<'valid' | 'invalid' | 'loading'>('loading');
  const [validationMessage, setValidationMessage] = useState('');
  const [importLoading, setImportLoading] = useState(false);
  
  // Handle file selection
  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setIsUploading(true);
    setValidationStatus('loading');
    setValidationMessage('');
    setParsedClasses([]);
    
    try {
      // Read the file
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const csvContent = e.target?.result as string;
          
          // Parse the CSV
          const classes = parseClassesCSV(csvContent);
          
          if (classes.length === 0) {
            setValidationStatus('invalid');
            setValidationMessage('No valid classes found in the CSV file.');
          } else {
            setParsedClasses(classes);
            setValidationStatus('valid');
          }
        } catch (error) {
          setValidationStatus('invalid');
          setValidationMessage((error as Error).message);
        } finally {
          setIsUploading(false);
        }
      };
      
      reader.onerror = () => {
        setValidationStatus('invalid');
        setValidationMessage('Error reading the file.');
        setIsUploading(false);
      };
      
      reader.readAsText(selectedFile);
    } catch (error) {
      setValidationStatus('invalid');
      setValidationMessage((error as Error).message);
      setIsUploading(false);
    }
  }, []);
  
  // Handle file removal
  const handleRemoveFile = useCallback(() => {
    setFile(null);
    setParsedClasses([]);
  }, []);
  
  // Handle class import
  const handleImportClasses = useCallback(() => {
    if (parsedClasses.length > 0) {
      setImportLoading(true);
      
      // Simulate a short loading time for better UX
      setTimeout(() => {
        setClasses(parsedClasses);
        setImportLoading(false);
      }, 500);
    }
  }, [parsedClasses, setClasses]);
  
  // Handle template download
  const handleDownloadTemplate = useCallback(() => {
    // Create template CSV content
    const templateContent = `name,grade,day_conflicts,period_conflicts,required_date,required_period
1-101,1,"Monday,Wednesday","3,5","2025-03-15,2025-03-22","2,4"
2-202,2,"Tuesday,Thursday","1,4",,`;
    
    // Create a blob and download link
    const blob = new Blob([templateContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'class_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, []);
  
  return (
    <div className="p-4 max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Upload Class Data</h2>
      
      {!file ? (
        <>
          <DropZone onFileSelect={handleFileSelect} isUploading={isUploading} />
          <TemplateDownload onDownload={handleDownloadTemplate} />
        </>
      ) : (
        <>
          <FileInfo 
            file={file}
            onRemove={handleRemoveFile}
            validationStatus={validationStatus}
            validationMessage={validationMessage}
          />
          
          {validationStatus === 'valid' && (
            <ClassPreview
              classes={parsedClasses}
              onImport={handleImportClasses}
              isLoading={importLoading}
            />
          )}
        </>
      )}
    </div>
  );
};