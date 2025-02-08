from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime

class TimeSlot(BaseModel):
    dayOfWeek: int  # 1-5 (Monday-Friday)
    period: int     # 1-8 (school periods)

class WeeklySchedule(BaseModel):
    conflicts: List[TimeSlot]         # Recurring weekly conflicts
    preferredPeriods: List[TimeSlot]  # Preferred time slots
    requiredPeriods: List[TimeSlot]   # Required time slots
    avoidPeriods: List[TimeSlot]      # Periods to avoid if possible
    preferenceWeight: float = 1.0     # Weight for preferred period satisfaction (default: 1.0)
    avoidanceWeight: float = 1.0      # Weight for avoid period penalties (default: 1.0)

class Class(BaseModel):
    id: str            # e.g., "1-409"
    name: str          # e.g., "1-409"
    grade: str         # Pre-K through 5
    weeklySchedule: WeeklySchedule

class TeacherAvailability(BaseModel):
    date: str          # ISO date string
    unavailableSlots: List[TimeSlot]
    preferredSlots: List[TimeSlot]
    avoidSlots: List[TimeSlot]

class ScheduleConstraints(BaseModel):
    maxClassesPerDay: int
    maxClassesPerWeek: int
    minPeriodsPerWeek: int
    maxConsecutiveClasses: Literal[1, 2]
    consecutiveClassesRule: Literal["hard", "soft"]

class ScheduleRequest(BaseModel):
    classes: List[Class]
    teacherAvailability: List[TeacherAvailability]
    startDate: str     # ISO date string
    endDate: str       # ISO date string
    constraints: ScheduleConstraints

class ScheduleAssignment(BaseModel):
    classId: str
    date: str         # ISO date string
    timeSlot: TimeSlot

class ScheduleMetadata(BaseModel):
    solver: Literal["cp-sat-stable", "cp-sat-dev"]  # Updated solver names
    duration: int    # milliseconds
    score: int      # optimization score

class ScheduleResponse(BaseModel):
    assignments: List[ScheduleAssignment]
    metadata: ScheduleMetadata
