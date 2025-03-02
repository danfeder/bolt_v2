import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render } from '../test-utils';
import { FileUpload } from '../../components/FileUpload';
import { parseClassesCSV } from '../../lib/csvParser';
import type { Class, ConflictPeriod, RequiredPeriod } from '../../types';

// Mock the csvParser module
jest.mock('../../lib/csvParser', () => ({
  parseClassesCSV: jest.fn()
}));

// Mock the scheduleStore
jest.mock('../../store/scheduleStore', () => ({
  useScheduleStore: jest.fn()
}));

// Import the mocked modules
const mockedParseClassesCSV = parseClassesCSV as jest.MockedFunction<typeof parseClassesCSV>;
const mockedScheduleStore = jest.requireMock('../../store/scheduleStore');

// Mock sample data
const mockClasses: Class[] = [
  {
    name: '1-101',
    grade: '1',
    conflicts: [{ dayOfWeek: 1, period: 3 }, { dayOfWeek: 2, period: 4 }] as ConflictPeriod[],
    required_periods: [] as RequiredPeriod[]
  },
  {
    name: '2-202',
    grade: '2',
    conflicts: [{ dayOfWeek: 3, period: 1 }, { dayOfWeek: 4, period: 2 }] as ConflictPeriod[],
    required_periods: [] as RequiredPeriod[]
  }
];

// Mock File class as it's not available in jest
global.File = class File {
  name: string;
  size: number;
  type: string;

  constructor(parts: any[], name: string, options: { type: string }) {
    this.name = name;
    this.size = 1024; // Mock file size as 1KB
    this.type = options.type;
  }
} as any;

// Create our own FileReader mock to simulate file reading
class MockFileReader {
  onload: ((ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((ev: ProgressEvent<FileReader>) => any) | null = null;
  result: string | ArrayBuffer | null = null;

  readAsText(file: Blob) {
    this.result = 'Mock CSV Content';
    setTimeout(() => {
      if (this.onload) {
        // Create a mock event with the correct structure
        const event = { 
          target: { 
            result: this.result 
          } 
        } as unknown as ProgressEvent<FileReader>;
        this.onload(event);
      }
    }, 0);
  }
}

// Replace the global FileReader with our mock
global.FileReader = MockFileReader as any;

// Create a mock for URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

describe('FileUpload Component', () => {
  const mockSetClasses = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Set up our mock store implementation
    mockedScheduleStore.useScheduleStore.mockImplementation((selector: any) => {
      // Mock state with setClasses method
      const mockState = {
        setClasses: mockSetClasses
      };
      
      // Handle selectors
      if (typeof selector === 'function') {
        return selector(mockState);
      }
      return mockState;
    });
    
    // Set up the parser mock to return sample classes
    mockedParseClassesCSV.mockReturnValue(mockClasses);
  });

  test('renders file upload interface correctly', () => {
    render(<FileUpload />);
    
    // Check for key UI elements
    expect(screen.getByText('File Format Guidelines')).toBeInTheDocument();
    expect(screen.getByText(/Drag & drop your CSV file/)).toBeInTheDocument();
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
    expect(screen.getByText('Download CSV Template')).toBeInTheDocument();
  });

  test('handles file selection and displays file info', async () => {
    render(<FileUpload />);
    
    // Create a mock file
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    // Get the file input and simulate a file selection
    const input = screen.getByLabelText(/Browse Files/);
    
    // Simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    // Check if file info is displayed
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
      expect(screen.getByText('1 KB')).toBeInTheDocument();
    });
    
    // Check if parser was called
    expect(mockedParseClassesCSV).toHaveBeenCalled();
  });

  test('displays preview when valid file is uploaded', async () => {
    render(<FileUpload />);
    
    // Create a mock file
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    // Get the file input and simulate a file selection
    const input = screen.getByLabelText(/Browse Files/);
    
    // Simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    // Check if preview is displayed
    await waitFor(() => {
      expect(screen.getByText(/Preview \(2 classes\)/)).toBeInTheDocument();
      expect(screen.getByText('1-101')).toBeInTheDocument();
      expect(screen.getByText('2-202')).toBeInTheDocument();
      expect(screen.getByText('Import Classes')).toBeInTheDocument();
    });
  });

  test('handles empty parsed results', async () => {
    // Make the parser return an empty array
    mockedParseClassesCSV.mockReturnValueOnce([]);
    
    render(<FileUpload />);
    
    // Create a mock file
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    // Get the file input and simulate a file selection
    const input = screen.getByLabelText(/Browse Files/);
    
    // Simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    // Check if error message is displayed
    await waitFor(() => {
      expect(screen.getByText('No valid classes found in the CSV file.')).toBeInTheDocument();
    });
  });

  test('handles parser errors', async () => {
    // Make the parser throw an error
    const errorMessage = 'Error parsing CSV: Invalid format';
    mockedParseClassesCSV.mockImplementationOnce(() => {
      throw new Error(errorMessage);
    });
    
    render(<FileUpload />);
    
    // Create a mock file
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    // Get the file input and simulate a file selection
    const input = screen.getByLabelText(/Browse Files/);
    
    // Simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    // Check if error message is displayed
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('imports classes when import button is clicked', async () => {
    // Mock setTimeout to execute immediately
    jest.useFakeTimers();
    
    render(<FileUpload />);
    
    // Create a mock file
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    // Get the file input and simulate a file selection
    const input = screen.getByLabelText(/Browse Files/);
    
    // Simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    // Wait for preview to be displayed
    await waitFor(() => {
      expect(screen.getByText('Import Classes')).toBeInTheDocument();
    });
    
    // Click the import button
    fireEvent.click(screen.getByText('Import Classes'));
    
    // Fast forward timers to trigger the setTimeout callback
    jest.runAllTimers();
    
    // Check if setClasses was called with the parsed classes
    expect(mockSetClasses).toHaveBeenCalledWith(mockClasses);
    
    // Restore timers
    jest.useRealTimers();
  });

  test('allows removing a selected file', async () => {
    render(<FileUpload />);
    
    // Create a mock file
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    
    // Get the file input and simulate a file selection
    const input = screen.getByLabelText(/Browse Files/);
    
    // Simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    // Wait for file info to be displayed
    await waitFor(() => {
      expect(screen.getByText('test.csv')).toBeInTheDocument();
    });
    
    // Click the remove button
    const removeButton = screen.getByRole('button', { name: /remove/i });
    fireEvent.click(removeButton);
    
    // Check if we're back to the upload interface
    expect(screen.getByText(/Drag & drop your CSV file/)).toBeInTheDocument();
  });

  test('downloads template when download button is clicked', () => {
    // Simplify the test by just mocking URL.createObjectURL
    const originalCreateObjectURL = URL.createObjectURL;
    URL.createObjectURL = jest.fn().mockReturnValue('mock-url');
    
    // Spy on document.createElement to verify it's called with the right tag
    const createElementSpy = jest.spyOn(document, 'createElement');
    
    render(<FileUpload />);
    
    // Click the download template button
    fireEvent.click(screen.getByText('Download CSV Template'));
    
    // Verify createElement was called with 'a'
    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(URL.createObjectURL).toHaveBeenCalled();
    
    // Cleanup
    URL.createObjectURL = originalCreateObjectURL;
    createElementSpy.mockRestore();
  });
});
