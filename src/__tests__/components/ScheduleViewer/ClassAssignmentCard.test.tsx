import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ClassAssignmentCard } from '../../../components/ScheduleViewer/ClassAssignmentCard';
import * as scheduleStoreModule from '../../../store/scheduleStore';

// Better mock for the Zustand store
jest.mock('../../../store/scheduleStore', () => {
  const originalModule = jest.requireActual('../../../store/scheduleStore');
  return {
    ...originalModule,
    useScheduleStore: jest.fn()
  };
});

describe('ClassAssignmentCard Component', () => {
  const mockAssignment = {
    name: 'TestClass',
    date: '2025-03-15',
    timeSlot: { dayOfWeek: 3, period: 4 }
  };
  
  beforeEach(() => {
    // Setup default mock implementation
    jest.spyOn(scheduleStoreModule, 'useScheduleStore').mockImplementation(() => ({
      classes: [{
        name: 'TestClass',
        grade: '3',
        conflicts: [],
        required_periods: []
      }]
    } as any));
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders basic assignment information', () => {
    render(<ClassAssignmentCard assignment={mockAssignment} />);
    
    expect(screen.getByText('TestClass')).toBeInTheDocument();
    expect(screen.getByText('(3)')).toBeInTheDocument(); // Grade display
  });
  
  test('shows conflict indicator when assignment has a conflict', () => {
    // Mock a class with conflicts
    jest.spyOn(scheduleStoreModule, 'useScheduleStore').mockImplementation(() => ({
      classes: [{
        name: 'TestClass',
        grade: '3',
        conflicts: [{ dayOfWeek: 3, period: 4 }], // Matches the assignment timeSlot
        required_periods: []
      }]
    } as any));
    
    render(<ClassAssignmentCard assignment={mockAssignment} />);
    
    // Check for the presence of conflict indicator (AlertCircle icon)
    // Since we can't easily test for the icon, we'll check for the title attribute
    const conflictIndicator = screen.getByTitle('This assignment has a conflict');
    expect(conflictIndicator).toBeInTheDocument();
  });
  
  test('shows required period indicator when assignment is a required period', () => {
    // Mock a class with required period
    jest.spyOn(scheduleStoreModule, 'useScheduleStore').mockImplementation(() => ({
      classes: [{
        name: 'TestClass',
        grade: '3',
        conflicts: [],
        required_periods: [{ date: '2025-03-15', period: 4 }] // Matches the assignment
      }]
    } as any));
    
    const { container } = render(<ClassAssignmentCard assignment={mockAssignment} />);
    
    // Check for the presence of the required period styling (ring-green-400)
    // This is a more brittle test, but will suffice for demonstration
    expect(container.querySelector('.ring-green-400')).not.toBeNull();
  });
  
  test('toggles details view when info button is clicked', () => {
    render(<ClassAssignmentCard assignment={mockAssignment} />);
    
    // Initially, details should not be visible
    expect(screen.queryByText('Period:')).not.toBeInTheDocument();
    
    // Click the info button to show details
    fireEvent.click(screen.getByLabelText('Show details'));
    
    // Details should now be visible
    expect(screen.getByText('Period:')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument(); // Period number
    expect(screen.getByText('Status:')).toBeInTheDocument();
    expect(screen.getByText('Normal')).toBeInTheDocument();
    
    // Click again to hide details
    fireEvent.click(screen.getByLabelText('Hide details'));
    
    // Details should be hidden again
    expect(screen.queryByText('Period:')).not.toBeInTheDocument();
  });
});
