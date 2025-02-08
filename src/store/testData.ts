import { Class, TeacherAvailability } from '../types';
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
      requiredPeriods: [],
      avoidPeriods: [
        { dayOfWeek: 5, period: 7 },  // Friday seventh period
        { dayOfWeek: 5, period: 8 },  // Friday eighth period
      ]
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
        { dayOfWeek: 5, period: 2 },  // Must be Friday second period
      ],
      avoidPeriods: []
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
      requiredPeriods: [],
      avoidPeriods: [
        { dayOfWeek: 1, period: 1 },  // Monday first period
        { dayOfWeek: 5, period: 8 },  // Friday eighth period
      ]
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
      requiredPeriods: [],
      avoidPeriods: [
        { dayOfWeek: 1, period: 7 },  // Monday seventh period
        { dayOfWeek: 2, period: 7 },  // Tuesday seventh period
        { dayOfWeek: 3, period: 7 },  // Wednesday seventh period
        { dayOfWeek: 4, period: 7 },  // Thursday seventh period
        { dayOfWeek: 5, period: 7 },  // Friday seventh period
      ]
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
      requiredPeriods: [],
      avoidPeriods: []
    }
  }
];

// Test Teacher Availability
export const testTeacherAvailability: TeacherAvailability[] = [
  {
    date: createDateStr(0),
    unavailableSlots: [
      { dayOfWeek: 1, period: 4 },  // Meeting
      { dayOfWeek: 1, period: 5 },  // Lunch
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