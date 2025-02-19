"""Test data generators for scheduler tests"""
from datetime import datetime, timedelta
from app.models import (
    ScheduleRequest, 
    Class, 
    ScheduleAssignment, 
    TimeSlot,
    ScheduleConstraints,
    InstructorAvailability,
    WeeklySchedule,
    RequiredPeriod,
    ConflictPeriod
)

class TimeSlotGenerator:
    """Generate test time slots"""
    
    @staticmethod
    def create_time_slot(period: int = 1) -> TimeSlot:
        return TimeSlot(dayOfWeek=1, period=period)

class ClassGenerator:
    """Generate test classes"""
    
    @staticmethod
    def create_class(
        name: str = "Test Class",
        instructor: str = "default_instructor",
        weekly_schedule: WeeklySchedule = None
    ) -> Class:
        return Class(
            id=name,  # Use name as ID for testing
            name=name,
            grade="Test",  # Add required grade field
            instructor=instructor,
            weeklySchedule=weekly_schedule or WeeklySchedule()
        )
        
    @staticmethod
    def create_classes(num_classes: int) -> list[Class]:
        return [
            ClassGenerator.create_class(f"Test Class {i+1}")
            for i in range(num_classes)
        ]

class InstructorAvailabilityGenerator:
    """Generate test instructor availability"""
    
    @staticmethod
    def create_availability(
        instructor: str = "default_instructor",
        date: datetime = None,
        periods: list[int] = None
    ) -> InstructorAvailability:
        if date is None:
            date = datetime.now()
        if periods is None:
            periods = []
            
        return InstructorAvailability(
            instructor=instructor,
            date=date,
            periods=periods,
            unavailableSlots=[],
            preferredSlots=[],
            avoidSlots=[]
        )

class ScheduleRequestGenerator:
    """Generate test schedule requests"""
    
    @staticmethod
    def create_request(
        num_classes: int = 1,
        num_weeks: int = 1,
        start_date: str = None,
        constraints: ScheduleConstraints = None
    ) -> ScheduleRequest:
        """
        Create a test schedule request.
        
        Args:
            num_classes: Number of classes to generate
            num_weeks: Number of weeks in schedule
            start_date: Optional start date (defaults to next Monday)
            constraints: Optional constraints (uses defaults if not provided)
            
        Returns:
            ScheduleRequest configured for testing
        """
        # Calculate dates
        if start_date is None:
            # Start next week Monday
            start = datetime.now()
            while start.weekday() != 0:  # Monday = 0
                start += timedelta(days=1)
            start_date = start.strftime("%Y-%m-%d")
            
        end = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(weeks=num_weeks)
        end_date = end.strftime("%Y-%m-%d")
        
        # Create default constraints if none provided
        if constraints is None:
            constraints = ScheduleConstraints(
                maxClassesPerDay=3,
                maxClassesPerWeek=12,
                minPeriodsPerWeek=5,
                maxConsecutiveClasses=2,
                consecutiveClassesRule="soft",
                startDate=start_date,
                endDate=end_date
            )
        
        return ScheduleRequest(
            startDate=start_date,
            endDate=end_date,
            classes=ClassGenerator.create_classes(num_classes),
            constraints=constraints,
            instructorAvailability=[]
        )
