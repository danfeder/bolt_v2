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
        
    @staticmethod
    def create_daily_pattern(period: int) -> list[TimeSlot]:
        """
        Create a pattern of TimeSlots for a specific period across all weekdays
        
        Args:
            period: The period number to create slots for
            
        Returns:
            List of TimeSlots, one for each weekday with the specified period
        """
        return [
            TimeSlot(dayOfWeek=day, period=period)
            for day in range(1, 6)  # Monday=1 through Friday=5
        ]

class ClassGenerator:
    """Generate test classes"""
    
    @staticmethod
    def create_class(
        name: str = "Test Class",
        class_id: str = None,
        instructor: str = "default_instructor",
        weekly_schedule: WeeklySchedule = None
    ) -> Class:
        # Handle both field naming conventions (id/classId)
        class_args = {
            "name": name,
            "grade": "Test",  # Add required grade field
            "instructor": instructor,
            "weeklySchedule": weekly_schedule or WeeklySchedule()
        }
        
        # Add ID field with the appropriate name
        id_value = class_id or name
        
        # Try both field names to handle different model versions
        try:
            return Class(id=id_value, **class_args)
        except TypeError:
            try:
                return Class(classId=id_value, **class_args)
            except TypeError:
                # If neither works, just return with the args we have
                # The model should have at least one of these fields
                return Class(**class_args)
        
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

    @staticmethod
    def create_weekly_availability(
        start_date: datetime,
        weeks: int = 1,
        unavailable_pattern: list[TimeSlot] = None
    ) -> list[InstructorAvailability]:
        """
        Create instructor availability for a specified number of weeks
        
        Args:
            start_date: Starting date for availability
            weeks: Number of weeks to generate
            unavailable_pattern: Optional list of TimeSlots representing unavailable periods
            
        Returns:
            List of InstructorAvailability objects
        """
        availabilities = []
        current_date = start_date
        
        for _ in range(weeks * 5):  # 5 days per week
            # Skip weekends
            while current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                current_date += timedelta(days=1)
            
            # Default to all periods available (1-8)
            periods = list(range(1, 9))
            
            # Remove unavailable periods for this day if specified
            if unavailable_pattern:
                for slot in unavailable_pattern:
                    if slot.dayOfWeek == current_date.weekday() + 1:
                        if slot.period in periods:
                            periods.remove(slot.period)
            
            availabilities.append(
                InstructorAvailability(
                    date=current_date,
                    periods=periods,
                    unavailableSlots=[],
                    preferredSlots=[],
                    avoidSlots=[]
                )
            )
            
            current_date += timedelta(days=1)
            
        return availabilities

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
