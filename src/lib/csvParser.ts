import { Class, WeeklySchedule, TimeSlot } from '../types';

const parsePeriodsString = (periodsStr: string): number[] => {
  // Remove any quotes and extra whitespace
  const cleaned = periodsStr.replace(/['"]/g, '').trim();
  
  // If empty, return empty array
  if (!cleaned) return [];
  
  // Split by comma and convert to numbers, handling whitespace
  return cleaned.split(',').map(p => parseInt(p.trim(), 10))
    .filter(n => !isNaN(n)); // Filter out any invalid numbers
};

export const parseClassesCSV = (csvContent: string): Class[] => {
  const lines = csvContent.trim().split('\n');
  
  // Skip header row
  return lines.slice(1).map(line => {
    // Split the line by commas, but handle quoted values
    const fields: string[] = [];
    let field = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        fields.push(field.trim());
        field = '';
      } else {
        field += char;
      }
    }
    fields.push(field.trim()); // Add the last field
    
    // Extract grade from class name
    const className = fields[0];
    let grade: string;
    
    if (className.startsWith('PK')) {
      grade = 'Pre-K';
    } else if (className.startsWith('K')) {
      grade = className.includes(',') ? 'multiple' : 'K';
    } else if (className.includes(',')) {
      grade = 'multiple';
    } else {
      grade = className.split('-')[0];
    }
    
    // Parse conflicts for each day
    const conflicts: TimeSlot[] = [];
    
    // Process each day's conflicts (fields 1-5 are Mon-Fri)
    for (let dayIndex = 0; dayIndex < 5; dayIndex++) {
      const periodsStr = fields[dayIndex + 1]; // +1 because first field is class name
      if (periodsStr) {
        const periods = parsePeriodsString(periodsStr);
        periods.forEach(period => {
          if (!isNaN(period)) {
            conflicts.push({
              dayOfWeek: dayIndex + 1, // 1-5 for Monday-Friday
              period
            });
          }
        });
      }
    }
    
    // Create the weekly schedule
    const weeklySchedule: WeeklySchedule = {
      conflicts,
      preferredPeriods: [], // Initialize empty
      requiredPeriods: [],  // Initialize empty
      avoidPeriods: []      // Initialize empty
    };
    
    return {
      id: className,
      name: className,
      grade,
      weeklySchedule
    };
  });
};