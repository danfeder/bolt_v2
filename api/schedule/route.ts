import { NextRequest, NextResponse } from 'next/server';
import { ScheduleRequest, ScheduleResponse } from '../lib/types';
import { createSchedule } from '../lib/or-tools';

export const runtime = 'edge';

export async function POST(request: NextRequest) {
  try {
    const data: ScheduleRequest = await request.json();

    // Validate request data
    if (!isValidScheduleRequest(data)) {
      return NextResponse.json(
        { error: 'Invalid request data' },
        { status: 400 }
      );
    }

    // Generate schedule using OR-Tools
    const schedule = await createSchedule(data);

    const response: ScheduleResponse = {
      assignments: schedule.assignments,
      metadata: {
        solver: 'or-tools',
        duration: schedule.duration,
        score: schedule.score
      }
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Schedule generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate schedule' },
      { status: 500 }
    );
  }
}

function isValidScheduleRequest(data: any): data is ScheduleRequest {
  return (
    data &&
    Array.isArray(data.classes) &&
    Array.isArray(data.teacherAvailability) &&
    data.constraints &&
    typeof data.constraints === 'object'
  );
}
