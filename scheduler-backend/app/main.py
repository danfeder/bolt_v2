from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import csv
from typing import List
import traceback
import sys

from .models import (
    ScheduleRequest, 
    ScheduleResponse, 
    Class, 
    WeeklySchedule,
    ScheduleConstraints,
    TimeSlot
)
from .scheduler import create_schedule_stable, create_schedule_dev

app = FastAPI(title="Gym Class Scheduler")

# Add CORS middleware with specific frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # Vite alternate port
        "http://127.0.0.1:5174",
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_periods(period_str: str) -> List[int]:
    """Parse period string like '1, 3' or '2' into list of integers"""
    if not period_str:
        return []
    try:
        # Remove quotes and split by comma
        return [int(p.strip()) for p in period_str.replace('"', '').split(',')]
    except ValueError as e:
        print(f"Error parsing periods '{period_str}': {e}", file=sys.stderr)
        return []

def load_classes_from_csv() -> List[Class]:
    classes = []
    try:
        with open('data/Schedule_From_Json_Corrected.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract class name and grade
                class_name = row['Class']
                if class_name.startswith('PK'):
                    grade = 'Pre-K'
                elif class_name.startswith('K'):
                    grade = class_name.split(',')[0] if ',' in class_name else 'K'
                else:
                    grade = class_name.split('-')[0] if '-' in class_name else class_name.split(',')[0]
                
                # Parse preferred periods for each day
                conflicts = []
                for day, periods in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']):
                    day_periods = parse_periods(row[periods])
                    for period in day_periods:
                        conflicts.append(TimeSlot(
                            dayOfWeek=day + 1,  # 1-5 for Monday-Friday
                            period=period
                        ))
                
                classes.append(Class(
                    id=class_name,
                    name=class_name,
                    grade=grade,
                    weeklySchedule=WeeklySchedule(
                        conflicts=conflicts,
                        preferredPeriods=[],
                        requiredPeriods=[],
                        avoidPeriods=[]
                    )
                ))
        return classes
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise

@app.post("/schedule", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleRequest,
    version: str = "stable"
) -> ScheduleResponse:
    """Generate a schedule based on the given constraints"""
    try:
        if version == "stable":
            return create_schedule_stable(request)
        elif version == "dev":
            return create_schedule_dev(request)
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown version: {version}. Available versions:\n"
                    "- stable: Basic scheduling without class limits\n"
                    "- dev: Full scheduling with class limits and required periods"
                )
            )
    except Exception as e:
        print(f"Error in generate_schedule: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/test-schedule")
async def test_schedule(version: str = "stable"):
    """Test endpoint using actual class data from CSV with test required periods"""
    try:
        # Get today's date and next 30 days for scheduling window
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30)
        
        # Load classes from CSV
        print("Loading classes from CSV...", file=sys.stderr)
        classes = load_classes_from_csv()
        print(f"Loaded {len(classes)} classes from CSV", file=sys.stderr)
        
        # Add test required periods to some classes
        test_required_periods = {
            # Simple required period case
            "2-411": [TimeSlot(dayOfWeek=5, period=1)],  # Must be Friday period 1
            
            # Required period that conflicts with teacher availability
            "3-416": [TimeSlot(dayOfWeek=1, period=4)],  # Must be Monday period 4
            
            # Required period that doesn't conflict
            "K-309": [TimeSlot(dayOfWeek=5, period=3)]  # Must be Friday period 3
        }
        
        # Update classes with required periods
        for class_obj in classes:
            if class_obj.id in test_required_periods:
                class_obj.weeklySchedule.requiredPeriods = test_required_periods[class_obj.id]
                print(f"Added required periods for {class_obj.id}: {test_required_periods[class_obj.id]}")
        
        # Add test teacher availability
        # Create teacher availability for the first week (Monday-Friday)
        test_teacher_availability = []
        current_date = start_date
        
        # Skip to next Monday if we're starting on a weekend
        while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            current_date += timedelta(days=1)
        
        # Add availability for Monday-Friday
        for _ in range(5):
            test_teacher_availability.append({
                "date": current_date.isoformat(),
                "unavailableSlots": [
                    TimeSlot(dayOfWeek=current_date.weekday() + 1, period=4),  # Period 4 unavailable every day
                    TimeSlot(dayOfWeek=current_date.weekday() + 1, period=5),  # Period 5 unavailable every day
                ],
                "preferredSlots": [
                    TimeSlot(dayOfWeek=current_date.weekday() + 1, period=2),
                    TimeSlot(dayOfWeek=current_date.weekday() + 1, period=3)
                ],
                "avoidSlots": [
                    TimeSlot(dayOfWeek=current_date.weekday() + 1, period=7),
                    TimeSlot(dayOfWeek=current_date.weekday() + 1, period=8)
                ]
            })
            current_date += timedelta(days=1)
            
            # Stop if we hit the weekend
            if current_date.weekday() >= 5:
                break
        
        # Create test request with actual class data and test constraints
        test_request = ScheduleRequest(
            classes=classes,
            teacherAvailability=test_teacher_availability,
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            constraints=ScheduleConstraints(
                maxClassesPerDay=4,
                maxClassesPerWeek=16,
                minPeriodsPerWeek=1,
                maxConsecutiveClasses=1,
                consecutiveClassesRule="soft"
            )
        )
        
        print(f"Created test request with {len(test_request.classes)} classes", file=sys.stderr)
        print("Required periods summary:")
        for class_obj in test_request.classes:
            if class_obj.weeklySchedule.requiredPeriods:
                print(f"  {class_obj.id}: {class_obj.weeklySchedule.requiredPeriods}")
        
        return await generate_schedule(test_request, version)
    except Exception as e:
        print(f"Error in test_schedule: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate test schedule: {str(e)}"
        )
