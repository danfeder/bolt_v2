import { Class, TeacherAvailability, ScheduleMetadata } from '../types';
import { addDays, format } from 'date-fns';

// Helper to create dates for teacher availability
const createDateStr = (daysToAdd: number) => 
  format(addDays(new Date(), daysToAdd), 'yyyy-MM-dd');

// Test Classes
export const testClasses: Class[] = [
  {
    id: '1-101',
    name: '1-101',
    grade: '1',
    weeklySchedule: {
      conflicts: [
        { dayOfWeek: 1, period: 1 },  // Monday first period
        { dayOfWeek: 3, period: 4 },  // Wednesday fourth period
      ],
      preferredPeriods: [
        { dayOfWeek: 2, period: 2 },  // Tuesday second period
        { dayOfWeek: 4, period: 3 },  // Thursday third period
      ],
      requiredPeriods: [],  // No required periods - basic case
      avoidPeriods: [
        { dayOfWeek: 5, period: 7 },  // Friday seventh period
        { dayOfWeek: 5, period: 8 },  // Friday eighth period
      ],
      preferenceWeight: 1.5,  // Strong preference for preferred periods
      avoidanceWeight: 1.2    // Moderate avoidance weight
    }
  },
  {
    id: '2-205',
    name: '2-205',
    grade: '2',
    weeklySchedule: {
      conflicts: [
        { dayOfWeek: 2, period: 5 },  // Tuesday fifth period (lunch)
        { dayOfWeek: 4, period: 5 },  // Thursday fifth period
      ],
      preferredPeriods: [
        { dayOfWeek: 1, period: 3 },  // Monday third period
        { dayOfWeek: 3, period: 3 },  // Wednesday third period
      ],
      requiredPeriods: [
        { dayOfWeek: 5, period: 2 },  // Must be Friday second period - simple required period case
      ],
      avoidPeriods: [],
      preferenceWeight: 2.0,  // Very strong preference for period 3
      avoidanceWeight: 1.0    // Default avoidance weight
    }
  },
  {
    id: '3-301',
    name: '3-301',
    grade: '3',
    weeklySchedule: {
      conflicts: [
        { dayOfWeek: 1, period: 6 },  // Monday sixth period
        { dayOfWeek: 3, period: 6 },  // Wednesday sixth period
        { dayOfWeek: 5, period: 6 },  // Friday sixth period
      ],
      preferredPeriods: [
        { dayOfWeek: 2, period: 4 },  // Tuesday fourth period
        { dayOfWeek: 4, period: 4 },  // Thursday fourth period
      ],
      requiredPeriods: [
        { dayOfWeek: 1, period: 4 }   // Must be Monday fourth period - conflicts with teacher availability
      ],
      avoidPeriods: [
        { dayOfWeek: 1, period: 1 },  // Monday first period
        { dayOfWeek: 5, period: 8 },  // Friday eighth period
      ],
      preferenceWeight: 1.0,  // Default preference weight
      avoidanceWeight: 2.0    // Strong avoidance weight
    }
  },
  {
    id: 'K-102',
    name: 'K-102',
    grade: 'K',
    weeklySchedule: {
      conflicts: [
        { dayOfWeek: 2, period: 3 },  // Tuesday third period
        { dayOfWeek: 4, period: 3 },  // Thursday third period
      ],
      preferredPeriods: [
        { dayOfWeek: 1, period: 2 },  // Monday second period
        { dayOfWeek: 3, period: 2 },  // Wednesday second period
        { dayOfWeek: 5, period: 2 },  // Friday second period
      ],
      requiredPeriods: [
        { dayOfWeek: 5, period: 2 }   // Must be Friday second period - conflicts with 2-205's required period
      ],
      avoidPeriods: [],
      preferenceWeight: 1.8,  // Strong preference for period 2
      avoidanceWeight: 1.0    // Default avoidance weight
    }
  },
  {
    id: 'PK-A',
    name: 'PK-A',
    grade: 'Pre-K',
    weeklySchedule: {
      conflicts: [
        { dayOfWeek: 1, period: 8 },  // Monday eighth period
        { dayOfWeek: 2, period: 8 },  // Tuesday eighth period
        { dayOfWeek: 3, period: 8 },  // Wednesday eighth period
        { dayOfWeek: 4, period: 8 },  // Thursday eighth period
        { dayOfWeek: 5, period: 8 },  // Friday eighth period
      ],
      preferredPeriods: [
        { dayOfWeek: 1, period: 1 },  // Monday first period
        { dayOfWeek: 2, period: 1 },  // Tuesday first period
        { dayOfWeek: 3, period: 1 },  // Wednesday first period
        { dayOfWeek: 4, period: 1 },  // Thursday first period
        { dayOfWeek: 5, period: 1 },  // Friday first period
      ],
      requiredPeriods: [],  // No required periods - basic case
      avoidPeriods: [],
      preferenceWeight: 2.5,  // Very strong preference for first period
      avoidanceWeight: 1.0    // Default avoidance weight
    }
  }
];

// Test Schedule Metadata with Distribution Metrics
export const testScheduleMetadata: ScheduleMetadata = {
  solver: 'cp-sat-dev',
  duration: 1250,  // 1.25 seconds
  score: 15750,
  distribution: {
    weekly: {
      variance: 0.75,
      classesPerWeek: {
        "0": 12,
        "1": 13,
        "2": 11,
        "3": 14
      },
      score: -75  // -100 * variance
    },
    daily: {
      byDate: {
        "2025-02-10": {  // Week 1 Monday
          periodSpread: 0.85,
          teacherLoadVariance: 0.5,
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
          teacherLoadVariance: 0.3,
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
          teacherLoadVariance: 0.8,
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
      score: -425  // Sum of spread penalties (-200 * (1-spread)) and load penalties (-150 * variance)
    },
    totalScore: -500  // weekly.score + daily.score
  }
};

// Test Teacher Availability
export const testTeacherAvailability: TeacherAvailability[] = [
  {
    date: createDateStr(0),
    unavailableSlots: [
      { dayOfWeek: 1, period: 4 },  // Meeting (conflicts with 3-301's required period)
      { dayOfWeek: 1, period: 5 },  // Lunch
      { dayOfWeek: 5, period: 2 },  // Meeting (conflicts with 2-205 and K-102's required periods)
    ],
    preferredSlots: [
      { dayOfWeek: 1, period: 2 },
      { dayOfWeek: 1, period: 3 },
    ],
    avoidSlots: [
      { dayOfWeek: 1, period: 7 },
      { dayOfWeek: 1, period: 8 },
    ]
  },
  {
    date: createDateStr(1),
    unavailableSlots: [
      { dayOfWeek: 2, period: 5 },  // Lunch
    ],
    preferredSlots: [
      { dayOfWeek: 2, period: 1 },
      { dayOfWeek: 2, period: 2 },
    ],
    avoidSlots: [
      { dayOfWeek: 2, period: 7 },
      { dayOfWeek: 2, period: 8 },
    ]
  },
  {
    date: createDateStr(2),
    unavailableSlots: [
      { dayOfWeek: 3, period: 5 },  // Lunch
    ],
    preferredSlots: [
      { dayOfWeek: 3, period: 2 },
      { dayOfWeek: 3, period: 3 },
    ],
    avoidSlots: [
      { dayOfWeek: 3, period: 7 },
      { dayOfWeek: 3, period: 8 },
    ]
  }
];
