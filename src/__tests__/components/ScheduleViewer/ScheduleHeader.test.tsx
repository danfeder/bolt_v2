import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScheduleHeader } from '../../../components/ScheduleViewer/ScheduleHeader';

describe('ScheduleHeader Component', () => {
  const mockProps = {
    viewMode: 'calendar' as const,
    onViewModeChange: jest.fn(),
    scheduleInterval: {
      start: new Date('2025-03-01'),
      end: new Date('2025-04-01')
    },
    currentWeek: new Date('2025-03-10'),
    setCurrentWeek: jest.fn()
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders correctly in calendar mode', () => {
    render(<ScheduleHeader {...mockProps} />);
    
    expect(screen.getByText('Gym Class Schedule')).toBeInTheDocument();
    expect(screen.getByText(/Week of/)).toBeInTheDocument();
    expect(screen.getByText('List View')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });
  
  test('renders correctly in list mode', () => {
    render(<ScheduleHeader {...{...mockProps, viewMode: 'list'}} />);
    
    expect(screen.getByText('Gym Class Schedule')).toBeInTheDocument();
    expect(screen.queryByText(/Week of/)).not.toBeInTheDocument(); // Week navigation not shown in list mode
    expect(screen.getByText('Calendar View')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });
  
  test('calls onViewModeChange when view toggle button is clicked', () => {
    render(<ScheduleHeader {...mockProps} />);
    
    fireEvent.click(screen.getByText('List View'));
    expect(mockProps.onViewModeChange).toHaveBeenCalledTimes(1);
  });
  
  test('navigates to previous week when previous button clicked', () => {
    render(<ScheduleHeader {...mockProps} />);
    
    fireEvent.click(screen.getByLabelText('Previous week'));
    expect(mockProps.setCurrentWeek).toHaveBeenCalledTimes(1);
  });
  
  test('navigates to next week when next button clicked', () => {
    render(<ScheduleHeader {...mockProps} />);
    
    fireEvent.click(screen.getByLabelText('Next week'));
    expect(mockProps.setCurrentWeek).toHaveBeenCalledTimes(1);
  });
  
  test('export button shows alert message', () => {
    // Mock window.alert
    const originalAlert = window.alert;
    window.alert = jest.fn();
    
    render(<ScheduleHeader {...mockProps} />);
    
    fireEvent.click(screen.getByText('Export'));
    expect(window.alert).toHaveBeenCalledWith('Export functionality coming soon!');
    
    // Restore original alert
    window.alert = originalAlert;
  });
});
