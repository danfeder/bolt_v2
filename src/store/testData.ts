import { Class, InstructorAvailability, ScheduleMetadata } from '../types';
import { addDays, format } from 'date-fns';

// Helper to create dates for availability
const createDateStr = (daysToAdd: number) => 
  format(addDays(new Date(), daysToAdd), 'yyyy-MM-dd');

// Test Classes
export const testClasses: Class[] = [
  {
    name: '1-101',
    grade: '1',
    conflicts: [
      { dayOfWeek: 1, period: 1 },  // Monday first period
      { dayOfWeek: 3, period: 4 },  // Wednesday fourth period
    ],
    required_periods: []  // No required periods - basic case
  },
  {
    name: '2-205',
    grade: '2',
    conflicts: [
      { dayOfWeek: 2, period: 5 },  // Tuesday fifth period (lunch)
      { dayOfWeek: 4, period: 5 },  // Thursday fifth period
    ],
    required_periods: [
      { date: createDateStr(4), period: 2 }  // Must be Friday second period
    ]
  },
  {
    name: '3-301',
    grade: '3',
    conflicts: [
      { dayOfWeek: 1, period: 6 },  // Monday sixth period
      { dayOfWeek: 3, period: 6 },  // Wednesday sixth period
      { dayOfWeek: 5, period: 6 },  // Friday sixth period
    ],
    required_periods: [
      { date: createDateStr(0), period: 4 }  // Must be Monday fourth period
    ]
  },
  {
    name: 'K-102',
    grade: 'K',
    conflicts: [
      { dayOfWeek: 2, period: 3 },  // Tuesday third period
      { dayOfWeek: 4, period: 3 },  // Thursday third period
    ],
    required_periods: [
      { date: createDateStr(4), period: 2 }  // Must be Friday second period
    ]
  },
  {
    name: 'PK-A',
    grade: 'Pre-K',
    conflicts: [
      { dayOfWeek: 1, period: 8 },  // Monday eighth period
      { dayOfWeek: 2, period: 8 },  // Tuesday eighth period
      { dayOfWeek: 3, period: 8 },  // Wednesday eighth period
      { dayOfWeek: 4, period: 8 },  // Thursday eighth period
      { dayOfWeek: 5, period: 8 },  // Friday eighth period
    ],
    required_periods: []  // No required periods - basic case
  }
];

// Test Schedule Metadata with Distribution Metrics
export const testScheduleMetadata: ScheduleMetadata = {
  duration_ms: 1250,  // 1.25 seconds
  solutions_found: 5,
  score: 15750,
  gap: 0.15,
  distribution: {
    weekly: {
      variance: 0.75,
      classesPerWeek: {
        "1": 12,
        "2": 13,
        "3": 11,
        "4": 14
      },
      score: -75  // -100 * variance
    },
    daily: {
      "2025-02-10": {  // Week 1 Monday
        periodSpread: 0.85,
        classLoadVariance: 0.5,
        classesByPeriod: {
          "1": 1,
          "2": 1,
          "3": 2,
          "4": 1,
          "5": 0,
          "6": 1,
          "7": 0,
          "8": 0
        }
      },
      "2025-02-11": {  // Week 1 Tuesday
        periodSpread: 0.92,
        classLoadVariance: 0.3,
        classesByPeriod: {
          "1": 1,
          "2": 1,
          "3": 1,
          "4": 1,
          "5": 1,
          "6": 1,
          "7": 0,
          "8": 0
        }
      },
      "2025-02-12": {  // Week 1 Wednesday
        periodSpread: 0.78,
        classLoadVariance: 0.8,
        classesByPeriod: {
          "1": 2,
          "2": 0,
          "3": 1,
          "4": 1,
          "5": 0,
          "6": 1,
          "7": 1,
          "8": 0
        }
      }
    },
    totalScore: -500  // weekly.score + daily.score
  }
};

// Test Instructor Availability
export const testInstructorAvailability: InstructorAvailability[] = [
  {
    date: createDateStr(0),
    periods: [4, 5]  // Meeting during period 4, Lunch during period 5
  },
  {
    date: createDateStr(1),
    periods: [5]  // Lunch during period 5
  },
  {
    date: createDateStr(2),
    periods: [5]  // Lunch during period 5
  },
  {
    date: createDateStr(4),
    periods: [2]  // Meeting during period 2
  }
];
