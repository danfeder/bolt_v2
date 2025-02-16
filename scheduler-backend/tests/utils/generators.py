from datetime import datetime, timedelta
from typing import List, Optional
from app.models import (
    Class,
    TimeSlot,
    WeeklySchedule,
    InstructorAvailability,
    ScheduleConstraints,
    ScheduleRequest
)

class TimeSlotGenerator:
    @staticmethod
    def create_sequential_slots(count: int, start_day: int = 1, start_period: int = 1) -> List[TimeSlot]:
        """Create a sequence of time slots"""
        slots = []
        day = start_day
        period = start_period
        
        for _ in range(count):
            slots.append(TimeSlot(dayOfWeek=day, period=period))
            period += 1
            if period > 8:  # Move to next day if we exceed 8 periods
                period = 1
                day += 1
            if day > 5:  # Reset to Monday if we exceed Friday
                day = 1
        
        return slots

    @staticmethod
    def create_daily_pattern(period: int, days: Optional[List[int]] = None) -> List[TimeSlot]:
        """Create time slots for specified period across multiple days"""
        if days is None:
            days = list(range(1, 6))  # Monday through Friday
        return [TimeSlot(dayOfWeek=day, period=period) for day in days]

class WeeklyScheduleGenerator:
    @staticmethod
    def create_schedule(
        num_conflicts: int = 1,
        num_preferred: int = 1,
        num_required: int = 1,
        num_avoid: int = 1,
        preference_weight: float = 1.5,
        avoidance_weight: float = 1.2
    ) -> WeeklySchedule:
        """Create a weekly schedule with specified numbers of each type of period"""
        all_slots = TimeSlotGenerator.create_sequential_slots(20)  # Large pool to select from
        
        return WeeklySchedule(
            conflicts=all_slots[:num_conflicts],
            preferredPeriods=all_slots[num_conflicts:num_conflicts + num_preferred],
            requiredPeriods=all_slots[num_conflicts + num_preferred:num_conflicts + num_preferred + num_required],
            avoidPeriods=all_slots[num_conflicts + num_preferred + num_required:num_conflicts + num_preferred + num_required + num_avoid],
            preferenceWeight=preference_weight,
            avoidanceWeight=avoidance_weight
        )

class ClassGenerator:
    @staticmethod
    def create_class(
        class_id: Optional[str] = None,
        grade: Optional[str] = None,
        weekly_schedule: Optional[WeeklySchedule] = None
    ) -> Class:
        """Create a class with specified or default parameters"""
        if class_id is None:
            class_id = f"test-{datetime.now().strftime('%H%M%S')}"
        if grade is None:
            grade = "1"
        if weekly_schedule is None:
            weekly_schedule = WeeklyScheduleGenerator.create_schedule()
            
        return Class(
            id=class_id,
            name=f"Test Class {class_id}",
            grade=grade,
            weeklySchedule=weekly_schedule
        )

    @staticmethod
    def create_multiple_classes(
        count: int,
        grade_prefix: str = "",
        with_conflicts: bool = True
    ) -> List[Class]:
        """Create multiple classes with optional grade prefix and conflicts"""
        classes = []
        for i in range(count):
            class_id = f"{grade_prefix}{i+1}"
            weekly_schedule = WeeklyScheduleGenerator.create_schedule(
                num_conflicts=1 if with_conflicts else 0
            )
            classes.append(ClassGenerator.create_class(
                class_id=class_id,
                grade=grade_prefix if grade_prefix else str(i+1),
                weekly_schedule=weekly_schedule
            ))
        return classes

class InstructorAvailabilityGenerator:
    @staticmethod
    def create_availability(
        date: Optional[datetime] = None,
        num_unavailable: int = 1,
        num_preferred: int = 1,
        num_avoid: int = 1
    ) -> InstructorAvailability:
        """Create instructor availability for a specific date"""
        if date is None:
            date = datetime.now()
            
        all_slots = TimeSlotGenerator.create_sequential_slots(20)
        periods = list(range(1, num_unavailable + 1))  # First n periods are unavailable
        
        return InstructorAvailability(
            date=date,
            periods=periods,  # Required field for unavailable periods
            unavailableSlots=all_slots[:num_unavailable],
            preferredSlots=all_slots[num_unavailable:num_unavailable + num_preferred],
            avoidSlots=all_slots[num_unavailable + num_preferred:num_unavailable + num_preferred + num_avoid]
        )

    @staticmethod
    def create_weekly_availability(
        start_date: datetime,
        weeks: int = 1,
        unavailable_pattern: Optional[List[TimeSlot]] = None
    ) -> List[InstructorAvailability]:
        """Create instructor availability for multiple weeks"""
        if unavailable_pattern is None:
            # Default to lunch periods (period 5) every day
            unavailable_pattern = TimeSlotGenerator.create_daily_pattern(5)
            
        availability = []
        current_date = start_date
        
        for _ in range(weeks * 5):  # 5 school days per week
            if current_date.weekday() < 5:  # Only add for weekdays
                availability.append(InstructorAvailabilityGenerator.create_availability(
                    date=current_date,
                    num_unavailable=len(unavailable_pattern)
                ))
            current_date += timedelta(days=1)
            
        return availability

class ScheduleRequestGenerator:
    @staticmethod
    def create_request(
        num_classes: int = 1,
        num_weeks: int = 2,
        constraints: Optional[ScheduleConstraints] = None,
        start_date: Optional[datetime] = None
    ) -> ScheduleRequest:
        """Create a complete schedule request"""
        if start_date is None:
            start_date = datetime.now()
        if constraints is None:
            end_date = start_date + timedelta(weeks=num_weeks)
            constraints = ScheduleConstraints(
                maxClassesPerDay=3,
                maxClassesPerWeek=8,
                minPeriodsPerWeek=1,
                maxConsecutiveClasses=1,
                consecutiveClassesRule="hard",
                startDate=start_date.strftime("%Y-%m-%d"),
                endDate=end_date.strftime("%Y-%m-%d")
            )
            
        end_date = start_date + timedelta(weeks=num_weeks)
        
        return ScheduleRequest(
            classes=ClassGenerator.create_multiple_classes(num_classes),
            instructorAvailability=InstructorAvailabilityGenerator.create_weekly_availability(
                start_date=start_date,
                weeks=num_weeks
            ),
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d"),
            constraints=constraints
        )
