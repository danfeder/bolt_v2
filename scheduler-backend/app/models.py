from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TimeSlot(BaseModel):
    dayOfWeek: int  # 1-7 for Monday-Sunday
    period: int     # 1-8 for periods

class WeeklySchedule(BaseModel):
    requiredPeriods: List[TimeSlot] = Field(default_factory=list)
    preferredPeriods: List[TimeSlot] = Field(default_factory=list)
    avoidPeriods: List[TimeSlot] = Field(default_factory=list)
    conflicts: List[TimeSlot] = Field(default_factory=list)  # Made optional with default empty list
    preferenceWeight: float = 1.0
    avoidanceWeight: float = 1.0

class Class(BaseModel):
    id: str
    name: str
    weeklySchedule: WeeklySchedule

class TeacherAvailability(BaseModel):
    date: str
    unavailableSlots: List[TimeSlot] = Field(default_factory=list)

class ScheduleConstraints(BaseModel):
    maxClassesPerDay: int = Field(ge=1, le=8)
    maxClassesPerWeek: int = Field(ge=1)
    minPeriodsPerWeek: int = Field(ge=0)
    maxConsecutiveClasses: int = Field(ge=1, le=2)
    consecutiveClassesRule: str = Field(pattern='^(hard|soft)$')
    startDate: str  # ISO format date
    endDate: str    # ISO format date

class ScheduleAssignment(BaseModel):
    classId: str
    date: str  # ISO format date
    timeSlot: TimeSlot

class DistributionMetrics(BaseModel):
    weekly: Dict[str, Any]  # Includes variance, classesPerWeek, score
    daily: Dict[str, Any]   # Per-date metrics
    totalScore: float

class ScheduleMetadata(BaseModel):
    solver: str             # Name/version of solver used
    duration: int          # Time taken in milliseconds
    score: int            # Overall solution score
    status: str           # Solver status (OPTIMAL, FEASIBLE, etc)
    solutions_found: int  # Number of solutions found
    optimization_gap: float  # Gap between best solution and bound
    distribution: Optional[DistributionMetrics] = None

class ScheduleRequest(BaseModel):
    classes: List[Class]
    teacherAvailability: List[TeacherAvailability] = Field(default_factory=list)
    startDate: str  # ISO format date
    endDate: str    # ISO format date
    constraints: ScheduleConstraints

    class Config:
        json_schema_extra = {
            "example": {
                "classes": [{
                    "id": "MATH101",
                    "name": "Mathematics 101",
                    "weeklySchedule": {
                        "requiredPeriods": [],
                        "preferredPeriods": [],
                        "avoidPeriods": [],
                        "conflicts": [],
                        "preferenceWeight": 1.0,
                        "avoidanceWeight": 1.0
                    }
                }],
                "teacherAvailability": [],
                "startDate": "2025-02-10",
                "endDate": "2025-03-10",
                "constraints": {
                    "maxClassesPerDay": 4,
                    "maxClassesPerWeek": 16,
                    "minPeriodsPerWeek": 8,
                    "maxConsecutiveClasses": 1,
                    "consecutiveClassesRule": "soft",
                    "startDate": "2025-02-10",
                    "endDate": "2025-03-10"
                }
            }
        }

class ScheduleResponse(BaseModel):
    assignments: List[ScheduleAssignment]
    metadata: ScheduleMetadata
