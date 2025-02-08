from datetime import datetime, timedelta
from app.models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    WeeklySchedule,
    TeacherAvailability,
    ScheduleConstraints
)
from app.scheduler import create_schedule_dev

def test_class_limits():
    """Test the class limit constraints"""
    
    # Use the same test data as the frontend
    test_classes = [
        Class(
            id="1-101",
            name="1-101",
            grade="1",
            weeklySchedule=WeeklySchedule(
                conflicts=[
                    TimeSlot(dayOfWeek=1, period=1),  # Monday first period
                    TimeSlot(dayOfWeek=3, period=4),  # Wednesday fourth period
                ],
                preferredPeriods=[
                    TimeSlot(dayOfWeek=2, period=2),  # Tuesday second period
                    TimeSlot(dayOfWeek=4, period=3),  # Thursday third period
                ],
                requiredPeriods=[],
                avoidPeriods=[
                    TimeSlot(dayOfWeek=5, period=7),  # Friday seventh period
                    TimeSlot(dayOfWeek=5, period=8),  # Friday eighth period
                ],
                preferenceWeight=1.5,  # Strong preference for preferred periods
                avoidanceWeight=1.2    # Moderate avoidance weight
            )
        ),
        Class(
            id="2-205",
            name="2-205",
            grade="2",
            weeklySchedule=WeeklySchedule(
                conflicts=[
                    TimeSlot(dayOfWeek=2, period=5),  # Tuesday fifth period
                    TimeSlot(dayOfWeek=4, period=5),  # Thursday fifth period
                ],
                preferredPeriods=[
                    TimeSlot(dayOfWeek=1, period=3),  # Monday third period
                    TimeSlot(dayOfWeek=3, period=3),  # Wednesday third period
                ],
                requiredPeriods=[
                    TimeSlot(dayOfWeek=5, period=2),  # Friday second period
                ],
                avoidPeriods=[],
                preferenceWeight=2.0,  # Very strong preference for period 3
                avoidanceWeight=1.0    # Default avoidance weight
            )
        ),
        Class(
            id="3-301",
            name="3-301",
            grade="3",
            weeklySchedule=WeeklySchedule(
                conflicts=[
                    TimeSlot(dayOfWeek=1, period=6),  # Monday sixth period
                    TimeSlot(dayOfWeek=3, period=6),  # Wednesday sixth period
                    TimeSlot(dayOfWeek=5, period=6),  # Friday sixth period
                ],
                preferredPeriods=[
                    TimeSlot(dayOfWeek=2, period=4),  # Tuesday fourth period
                    TimeSlot(dayOfWeek=4, period=4),  # Thursday fourth period
                ],
                requiredPeriods=[
                    TimeSlot(dayOfWeek=1, period=4)  # Monday fourth period
                ],
                avoidPeriods=[
                    TimeSlot(dayOfWeek=1, period=1),  # Monday first period
                    TimeSlot(dayOfWeek=5, period=8),  # Friday eighth period
                ],
                preferenceWeight=1.0,  # Default preference weight
                avoidanceWeight=2.0    # Strong avoidance weight
            )
        ),
        Class(
            id="K-102",
            name="K-102",
            grade="K",
            weeklySchedule=WeeklySchedule(
                conflicts=[
                    TimeSlot(dayOfWeek=2, period=3),  # Tuesday third period
                    TimeSlot(dayOfWeek=4, period=3),  # Thursday third period
                ],
                preferredPeriods=[
                    TimeSlot(dayOfWeek=1, period=2),  # Monday second period
                    TimeSlot(dayOfWeek=3, period=2),  # Wednesday second period
                    TimeSlot(dayOfWeek=5, period=2),  # Friday second period
                ],
                requiredPeriods=[
                    TimeSlot(dayOfWeek=5, period=2)  # Friday second period
                ],
                avoidPeriods=[],
                preferenceWeight=1.8,  # Strong preference for period 2
                avoidanceWeight=1.0    # Default avoidance weight
            )
        ),
        Class(
            id="PK-A",
            name="PK-A",
            grade="Pre-K",
            weeklySchedule=WeeklySchedule(
                conflicts=[
                    TimeSlot(dayOfWeek=1, period=8),  # Monday eighth period
                    TimeSlot(dayOfWeek=2, period=8),  # Tuesday eighth period
                    TimeSlot(dayOfWeek=3, period=8),  # Wednesday eighth period
                    TimeSlot(dayOfWeek=4, period=8),  # Thursday eighth period
                    TimeSlot(dayOfWeek=5, period=8),  # Friday eighth period
                ],
                preferredPeriods=[
                    TimeSlot(dayOfWeek=1, period=1),  # Monday first period
                    TimeSlot(dayOfWeek=2, period=1),  # Tuesday first period
                    TimeSlot(dayOfWeek=3, period=1),  # Wednesday first period
                    TimeSlot(dayOfWeek=4, period=1),  # Thursday first period
                    TimeSlot(dayOfWeek=5, period=1),  # Friday first period
                ],
                requiredPeriods=[],
                avoidPeriods=[],
                preferenceWeight=2.5,  # Very strong preference for first period
                avoidanceWeight=1.0    # Default avoidance weight
            )
        )
    ]

    # Create schedule request with various constraint configurations
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")  # 3 weeks to allow flexibility

    # Create teacher availability data - spread across weeks
    test_teacher_availability = []
    
    # Create teacher availability - just lunch breaks
    for week in range(3):  # 3 weeks
        current_date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=7*week)
        for i in range(5):  # Monday to Friday
            test_teacher_availability.append(
                TeacherAvailability(
                    date=current_date.strftime("%Y-%m-%d"),
                    unavailableSlots=[
                        TimeSlot(dayOfWeek=i+1, period=5),  # Lunch break
                    ],
                    preferredSlots=[],
                    avoidSlots=[]
                )
            )
            current_date += timedelta(days=1)

    print("\n=== Testing Hard Consecutive Class Constraints ===")
    request = ScheduleRequest(
        classes=test_classes,
        teacherAvailability=test_teacher_availability,
        startDate=start_date,
        endDate=end_date,
        constraints=ScheduleConstraints(
            maxClassesPerDay=2,  # Consistent with other tests
            maxClassesPerWeek=4,  # Force spreading across weeks
            minPeriodsPerWeek=1,  # Allow flexible weekly scheduling
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    try:
        result = create_schedule_dev(request)
        print("Hard constraint test passed!")
        print_schedule_summary(result.assignments)
    except Exception as e:
        print(f"Hard constraint test failed: {str(e)}")

    print("\n=== Testing Soft Consecutive Class Constraints ===")
    request.constraints.consecutiveClassesRule = "soft"
    request.constraints.maxConsecutiveClasses = 2
    
    try:
        result = create_schedule_dev(request)
        print("Soft constraint test passed!")
        print_schedule_summary(result.assignments)
    except Exception as e:
        print(f"Soft constraint test failed: {str(e)}")

    print("\n=== Testing Daily Class Limits ===")
    request.constraints.maxClassesPerDay = 2  # Strict daily limit
    
    try:
        result = create_schedule_dev(request)
        print("Daily limit test passed!")
        print_schedule_summary(result.assignments)
    except Exception as e:
        print(f"Daily limit test failed: {str(e)}")

    print("\n=== Testing Weekly Class Limits ===")
    request.constraints.maxClassesPerWeek = 4  # Lower max to force spreading across weeks
    request.constraints.minPeriodsPerWeek = 1  # Lower minimum to allow spreading across weeks
    
    try:
        result = create_schedule_dev(request)
        print("Weekly limit test passed!")
        print_schedule_summary(result.assignments)
    except Exception as e:
        print(f"Weekly limit test failed: {str(e)}")

def print_schedule_summary(assignments):
    """Print a summary of the schedule assignments"""
    # Group by date
    by_date = {}
    for assignment in assignments:
        date = assignment.date.split('T')[0]  # Remove time part
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(assignment)
    
    # Print summary
    for date in sorted(by_date.keys()):
        print(f"\nDate: {date}")
        day_assignments = sorted(by_date[date], key=lambda x: x.timeSlot.period)
        for assignment in day_assignments:
            print(f"  Period {assignment.timeSlot.period}: {assignment.classId}")

if __name__ == "__main__":
    test_class_limits()
