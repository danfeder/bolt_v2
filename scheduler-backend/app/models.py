from typing import List, Optional, Dict
from pydantic import BaseModel, Field, RootModel
from datetime import datetime, time

class TimeSlot(BaseModel):
    dayOfWeek: int = Field(..., ge=1, le=5, description="Day of week (1=Monday, 5=Friday)")
    period: int = Field(..., ge=1, le=8, description="Period number (1-8)")
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "dayOfWeek": 1,
                "period": 1
            }
        }
    }

class RequiredPeriod(BaseModel):
    date: str
    period: int = Field(..., ge=1, le=8)
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "date": "2025-02-12",
                "period": 1
            }
        }
    }

class ConflictPeriod(BaseModel):
    dayOfWeek: int = Field(..., ge=1, le=5)
    period: int = Field(..., ge=1, le=8)
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "dayOfWeek": 1,
                "period": 1
            }
        }
    }

class Class(BaseModel):
    name: str
    grade: str = Field(..., description="Grade level (Pre-K through 5)")
    conflicts: List[ConflictPeriod] = []
    required_periods: List[RequiredPeriod] = []
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "name": "PK207",
                "grade": "Pre-K",
                "conflicts": [
                    {"dayOfWeek": 1, "period": 2},
                    {"dayOfWeek": 2, "period": 3}
                ],
                "required_periods": []
            }
        }
    }

class InstructorAvailability(BaseModel):
    date: datetime
    periods: List[int] = Field(..., description="List of periods when the instructor is unavailable")
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "date": "2025-02-12T00:00:00",
                "periods": [1, 2, 3]
            }
        }
    }

class ScheduleConstraints(BaseModel):
    maxClassesPerDay: int
    maxClassesPerWeek: int
    minPeriodsPerWeek: int
    maxConsecutiveClasses: int
    consecutiveClassesRule: str
    startDate: str
    endDate: str
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "maxClassesPerDay": 4,
                "maxClassesPerWeek": 16,
                "minPeriodsPerWeek": 8,
                "maxConsecutiveClasses": 2,
                "consecutiveClassesRule": "soft",
                "startDate": "2025-02-12",
                "endDate": "2025-03-14"
            }
        }
    }

class ScheduleRequest(BaseModel):
    classes: List[Class]
    instructorAvailability: List[InstructorAvailability]
    startDate: str
    endDate: str
    constraints: ScheduleConstraints
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "classes": [],
                "instructorAvailability": [],
                "startDate": "2025-02-12",
                "endDate": "2025-03-14",
                "constraints": {}
            }
        }
    }

class ScheduleAssignment(BaseModel):
    name: str = Field(..., description="Class name (e.g., PK207)")
    date: str
    timeSlot: TimeSlot
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "name": "PK207",
                "date": "2025-02-12",
                "timeSlot": {
                    "dayOfWeek": 1,
                    "period": 1
                }
            }
        }
    }

class ScheduleMetadata(BaseModel):
    duration_ms: int
    solutions_found: int
    score: float
    gap: float
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "duration_ms": 1000,
                "solutions_found": 1,
                "score": -857960000,
                "gap": -1.13
            }
        }
    }

class ScheduleResponse(BaseModel):
    assignments: List[ScheduleAssignment]
    metadata: ScheduleMetadata
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "assignments": [],
                "metadata": {
                    "duration_ms": 1000,
                    "solutions_found": 1,
                    "score": -857960000,
                    "gap": -1.13
                }
            }
        }
    }

class WeeklyDistributionMetrics(BaseModel):
    variance: float
    classesPerWeek: Dict[str, int]
    score: float

class DailyDistributionMetrics(BaseModel):
    periodSpread: float
    teacherLoadVariance: float
    classesByPeriod: Dict[str, int]

class DistributionMetrics(BaseModel):
    weekly: WeeklyDistributionMetrics
    daily: Dict[str, DailyDistributionMetrics]
    totalScore: float

    model_config = {
        'json_schema_extra': {
            "example": {
                "weekly": {
                    "variance": 0.5,
                    "classesPerWeek": {"1": 8, "2": 8, "3": 8, "4": 8},
                    "score": -50.0
                },
                "daily": {
                    "2025-02-12": {
                        "periodSpread": 0.8,
                        "teacherLoadVariance": 0.2,
                        "classesByPeriod": {"1": 2, "2": 1, "3": 1}
                    }
                },
                "totalScore": -75.0
            }
        }
    }

class WeightConfig(BaseModel):
    final_week_compression: int = Field(..., ge=0, le=10000, description="Weight for final week compression")
    day_usage: int = Field(..., ge=0, le=10000, description="Weight for day usage objective")
    daily_balance: int = Field(..., ge=0, le=10000, description="Weight for daily balance objective")
    preferred_periods: int = Field(..., ge=0, le=10000, description="Weight for preferred periods")
    distribution: int = Field(..., ge=0, le=10000, description="Weight for distribution objective")
    avoid_periods: int = Field(..., ge=-10000, le=0, description="Penalty for using avoided periods")
    earlier_dates: int = Field(..., ge=0, le=1000, description="Weight for earlier dates preference")

    model_config = {
        'json_schema_extra': {
            "example": {
                "final_week_compression": 3000,
                "day_usage": 2000,
                "daily_balance": 1500,
                "preferred_periods": 1000,
                "distribution": 1000,
                "avoid_periods": -500,
                "earlier_dates": 10
            }
        }
    }

    @property
    def weights_dict(self) -> dict:
        """Return weights as a dictionary for easy update"""
        return self.dict()
