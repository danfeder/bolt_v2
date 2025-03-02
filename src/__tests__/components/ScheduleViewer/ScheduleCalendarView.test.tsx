import React from 'react';
import { render, screen } from '@testing-library/react';
import { ScheduleCalendarView } from '../../../components/ScheduleViewer/ScheduleCalendarView';
import * as scheduleStoreModule from '../../../store/scheduleStore';

jest.mock('../../../store/scheduleStore', () => {
  const originalModule = jest.requireActual('../../../store/scheduleStore');
  return {
    ...originalModule,
    useScheduleStore: jest.fn()
  };
});

describe('ScheduleCalendarView Component', () => {
  const mockAssignments = [
    {
      name: 'Class1',
      date: '2025-03-02',
      timeSlot: { dayOfWeek: 1, period: 1 }
    },
    {
      name: 'Class2',
      date: '2025-03-02',
      timeSlot: { dayOfWeek: 1, period: 2 }
    },
    {
      name: 'Class3',
      date: '2025-03-03',
      timeSlot: { dayOfWeek: 2, period: 3 }
    }
  ];
  
  const mockClasses = [
    {
      name: 'Class1',
      grade: '3',
      conflicts: [],
      required_periods: []
    },
    {
      name: 'Class2',
      grade: '4',
      conflicts: [{ dayOfWeek: 1, period: 2 }],
      required_periods: []
    },
    {
      name: 'Class3',
      grade: '5',
      conflicts: [],
      required_periods: [{ date: '2025-03-03', period: 3 }]
    }
  ];
  
  const mockConstraints = {
    maxClassesPerDay: 3,
    maxClassesPerWeek: 10,
    minPeriodsPerWeek: 5,
    maxConsecutiveClasses: 2,
    consecutiveClassesRule: 'hard',
    startDate: '2025-03-01',
    endDate: '2025-04-01'
  };
  
  const mockCurrentWeek = new Date('2025-03-03'); // A Monday
  const mockSetCurrentWeek = jest.fn();
  
  const mockScheduleInterval = {
    start: new Date('2025-03-01'),
    end: new Date('2025-04-01')
  };
  
  beforeEach(() => {
    jest.spyOn(scheduleStoreModule, 'useScheduleStore').mockImplementation(() => ({
      classes: mockClasses,
      constraints: mockConstraints
    } as any));
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders calendar grid with correct days', () => {
    render(
      <ScheduleCalendarView 
        filteredAssignments={mockAssignments}
        currentWeek={mockCurrentWeek}
        setCurrentWeek={mockSetCurrentWeek}
        scheduleInterval={mockScheduleInterval}
      />
    );
    
    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('Tuesday')).toBeInTheDocument();
    expect(screen.getByText('Wednesday')).toBeInTheDocument();
    expect(screen.getByText('Thursday')).toBeInTheDocument();
    expect(screen.getByText('Friday')).toBeInTheDocument();
  });
  
  test('displays period rows in calendar', () => {
    render(
      <ScheduleCalendarView 
        filteredAssignments={mockAssignments}
        currentWeek={mockCurrentWeek}
        setCurrentWeek={mockSetCurrentWeek}
        scheduleInterval={mockScheduleInterval}
      />
    );
    
    for (let i = 1; i <= 8; i++) {
      expect(screen.getByText(i.toString())).toBeInTheDocument();
    }
  });
  
  test('displays assignments in calendar cells', () => {
    const mockAssignments = [
      {
        name: 'Class1',
        date: '2025-03-03', // Monday
        timeSlot: { dayOfWeek: 1, period: 1 }
      },
      {
        name: 'Class2',
        date: '2025-03-04', // Tuesday
        timeSlot: { dayOfWeek: 2, period: 2 }
      },
      {
        name: 'Class3',
        date: '2025-03-05', // Wednesday
        timeSlot: { dayOfWeek: 3, period: 3 }
      }
    ];
    
    jest.spyOn(scheduleStoreModule, 'useScheduleStore').mockImplementation(() => ({
      classes: [
        { name: 'Class1', grade: '3', conflicts: [], required_periods: [] },
        { name: 'Class2', grade: '4', conflicts: [], required_periods: [] },
        { name: 'Class3', grade: '5', conflicts: [], required_periods: [] }
      ]
    } as any));
    
    const { container } = render(
      <ScheduleCalendarView 
        filteredAssignments={mockAssignments}
        currentWeek={mockCurrentWeek}
        setCurrentWeek={mockSetCurrentWeek}
        scheduleInterval={mockScheduleInterval}
      />
    );
    
    expect(container.querySelector('table')).toBeInTheDocument();
    expect(container.querySelector('thead')).toBeInTheDocument();
    expect(container.querySelector('tbody')).toBeInTheDocument();
    
    const nonEmptyCells = Array.from(container.querySelectorAll('td')).filter(
      cell => cell.textContent && cell.textContent.trim().length > 0
    );
    
    expect(nonEmptyCells.length).toBeGreaterThan(0);
  });
  
  test('handles empty assignment list', () => {
    render(
      <ScheduleCalendarView 
        filteredAssignments={[]}
        currentWeek={mockCurrentWeek}
        setCurrentWeek={mockSetCurrentWeek}
        scheduleInterval={mockScheduleInterval}
      />
    );
    
    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    
    expect(screen.queryByText('Class1')).not.toBeInTheDocument();
  });
});
