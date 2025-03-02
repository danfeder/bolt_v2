import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScheduleListView } from '../../../components/ScheduleViewer/ScheduleListView';
import * as scheduleStoreModule from '../../../store/scheduleStore';

jest.mock('../../../store/scheduleStore', () => {
  const originalModule = jest.requireActual('../../../store/scheduleStore');
  return {
    ...originalModule,
    useScheduleStore: jest.fn()
  };
});

describe('ScheduleListView Component', () => {
  const mockAssignments = [
    {
      name: 'Class1',
      date: '2025-03-02',
      timeSlot: { dayOfWeek: 1, period: 1 }
    },
    {
      name: 'Class2',
      date: '2025-03-04',
      timeSlot: { dayOfWeek: 3, period: 2 }
    },
    {
      name: 'Class3',
      date: '2025-03-03',
      timeSlot: { dayOfWeek: 2, period: 3 }
    }
  ];
  
  beforeEach(() => {
    jest.spyOn(scheduleStoreModule, 'useScheduleStore').mockImplementation(() => ({
      classes: [
        { name: 'Class1', grade: '3', conflicts: [], required_periods: [] },
        { name: 'Class2', grade: '4', conflicts: [], required_periods: [] },
        { name: 'Class3', grade: '5', conflicts: [], required_periods: [] }
      ]
    } as any));
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders list view with assignments', () => {
    render(<ScheduleListView filteredAssignments={mockAssignments} />);
    
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Period')).toBeInTheDocument();
    expect(screen.getByText('Class')).toBeInTheDocument();
    expect(screen.getByText('Grade')).toBeInTheDocument();
    
    expect(screen.getByText('Class1')).toBeInTheDocument();
    expect(screen.getByText('Class2')).toBeInTheDocument();
    expect(screen.getByText('Class3')).toBeInTheDocument();
  });
  
  test('sorts assignments by date when header is clicked', () => {
    render(<ScheduleListView filteredAssignments={mockAssignments} />);
    
    fireEvent.click(screen.getByText('Date'));
    
    expect(screen.getByTestId('sort-indicator-date')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Date'));
    
    expect(screen.getByTestId('sort-indicator-date')).toBeInTheDocument();
  });
  
  test('sorts assignments by period when header is clicked', () => {
    render(<ScheduleListView filteredAssignments={mockAssignments} />);
    
    fireEvent.click(screen.getByText('Period'));
    
    expect(screen.getByTestId('sort-indicator-period')).toBeInTheDocument();
  });
  
  test('sorts assignments by class name when header is clicked', () => {
    render(<ScheduleListView filteredAssignments={mockAssignments} />);
    
    fireEvent.click(screen.getByText('Class'));
    
    expect(screen.getByTestId('sort-indicator-name')).toBeInTheDocument();
  });
  
  test('sorts assignments by grade when header is clicked', () => {
    render(<ScheduleListView filteredAssignments={mockAssignments} />);
    
    fireEvent.click(screen.getByText('Grade'));
    
    expect(screen.getByTestId('sort-indicator-grade')).toBeInTheDocument();
  });
  
  test('handles empty assignment list', () => {
    render(<ScheduleListView filteredAssignments={[]} />);
    
    expect(screen.getByText('No assignments match your filters.')).toBeInTheDocument();
  });
});
