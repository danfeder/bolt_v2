from typing import List, Optional, Dict, ForwardRef, Any, Union
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

class WeeklySchedule(BaseModel):
    conflicts: List[TimeSlot] = []
    preferredPeriods: List[TimeSlot] = []
    requiredPeriods: List[TimeSlot] = []
    avoidPeriods: List[TimeSlot] = []
    preferenceWeight: float = Field(default=1.5)
    avoidanceWeight: float = Field(default=1.2)
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "conflicts": [],
                "preferredPeriods": [],
                "requiredPeriods": [],
                "avoidPeriods": [],
                "preferenceWeight": 1.5,
                "avoidanceWeight": 1.2
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
    id: str = Field(..., description="Unique identifier for the class")
    name: str
    grade: str = Field(..., description="Grade level (Pre-K through 5)")
    gradeGroup: Optional[int] = Field(None, description="Numeric grade group (0=Pre-K, 1=K, 2-6=Grades 1-5)")
    equipmentNeeds: Optional[List[str]] = Field(default_factory=list, description="Equipment needed for this class")
    weeklySchedule: WeeklySchedule = Field(default_factory=WeeklySchedule)
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "id": "PK207",
                "name": "PK207",
                "grade": "Pre-K",
                "gradeGroup": 0,
                "equipmentNeeds": ["mats", "small balls"],
                "weeklySchedule": {
                    "conflicts": [],
                    "preferredPeriods": [],
                    "requiredPeriods": [],
                    "avoidPeriods": []
                }
            }
        }
    }
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Auto-populate grade group if not provided
        if self.gradeGroup is None:
            # Map grade levels to numeric values
            grade_map = {
                "Pre-K": 0,
                "K": 1,  # Kindergarten is standardized to "K"
                "1": 2,
                "2": 3,
                "3": 4,
                "4": 5,
                "5": 6
            }
            self.gradeGroup = grade_map.get(self.grade, 0)

class InstructorAvailability(BaseModel):
    date: datetime
    periods: List[int] = Field(..., description="List of periods when the instructor is unavailable")
    unavailableSlots: List[TimeSlot] = []
    preferredSlots: List[TimeSlot] = []
    avoidSlots: List[TimeSlot] = []
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "date": "2025-02-12T00:00:00",
                "periods": [1, 2, 3],
                "unavailableSlots": [],
                "preferredSlots": [],
                "avoidSlots": []
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
    allowConsecutiveClasses: bool = Field(default=True, description="If true, allows pairs of consecutive classes; if false, no consecutive classes allowed")
    requiredBreakPeriods: List[int] = Field(default_factory=list, description="List of periods that should be kept free (e.g., lunch periods)")
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "maxClassesPerDay": 4,
                "maxClassesPerWeek": 16,
                "minPeriodsPerWeek": 8,
                "maxConsecutiveClasses": 2,
                "consecutiveClassesRule": "soft",
                "startDate": "2025-02-12",
                "endDate": "2025-03-14",
                "allowConsecutiveClasses": True,
                "requiredBreakPeriods": [4]
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
    classId: Optional[str] = Field(None, description="Class ID (alternative to name)")
    date: str
    timeSlot: TimeSlot
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "name": "PK207",
                "classId": "class-123",
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
    distribution: Optional[Any] = None
    solver: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Duration in seconds, converted from milliseconds for backward compatibility."""
        return self.duration_ms / 1000.0
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "duration_ms": 1000,
                "solutions_found": 1,
                "score": -857960000,
                "gap": -1.13,
                "distribution": None,
                "solver": "cp-sat-unified",
                "error": None
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
                    "gap": -1.13,
                    "distribution": None,
                    "solver": "cp-sat-unified",
                    "error": None
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
    instructorLoadVariance: float  # Changed from teacherLoadVariance
    classesByPeriod: Dict[str, int]  # Using str keys for period numbers

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
                        "instructorLoadVariance": 0.2,
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
