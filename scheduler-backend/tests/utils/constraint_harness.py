from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ortools.sat.python import cp_model

from app.scheduling.core import SchedulerContext
from app.scheduling.constraints.base import BaseConstraint, ConstraintViolation
from app.models import (
    ScheduleRequest,
    InstructorAvailability,
    WeeklySchedule,
    RequiredPeriod,
    ConflictPeriod,
    ScheduleConstraints
)
from tests.utils.generators import (
    ClassGenerator,
    InstructorAvailabilityGenerator,
    TimeSlotGenerator,
    ScheduleRequestGenerator
)

class ConstraintTestHarness:
    """Test harness for isolating and testing individual constraints"""
    
    def __init__(self):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.variables: List[Dict[str, Any]] = []
        self.assignments: List[Dict[str, Any]] = []
        self._forced_assignments = {}  # Track forced assignments when constraints aren't applied
        
    def create_context(
        self,
        request: Optional[ScheduleRequest] = None,
        num_classes: int = 1,
        num_weeks: int = 1
    ) -> SchedulerContext:
        """
        Create a scheduler context for testing constraints.
        
        Args:
            request: Optional pre-configured ScheduleRequest
            num_classes: Number of classes if generating new request
            num_weeks: Number of weeks if generating new request
            
        Returns:
            SchedulerContext with model and variables set up
        """
        if request is None:
            # Create constraints with low limits to make violations easier to trigger
            constraints = ScheduleConstraints(
                maxClassesPerDay=2,  # Low limit to make violations more likely
                maxClassesPerWeek=8,  # Low limit to make violations more likely
                minPeriodsPerWeek=5,  # Reasonable minimum to test against
                maxConsecutiveClasses=2,
                consecutiveClassesRule="soft",
                startDate="2025-02-18",
                endDate="2025-02-25"
            )
            request = ScheduleRequestGenerator.create_request(
                num_classes=num_classes,
                num_weeks=num_weeks,
                constraints=constraints
            )
            
        # Create decision variables for each class and time slot
        start = datetime.strptime(request.startDate, "%Y-%m-%d")
        end = datetime.strptime(request.endDate, "%Y-%m-%d")
        current = start
        
        self.variables = []
        self._forced_assignments = {}  # Reset forced assignments
        
        while current <= end:
            if current.weekday() < 5:  # Weekdays only
                for period in range(1, 9):  # 8 periods per day
                    for class_obj in request.classes:
                        var = self.model.NewBoolVar(
                            f"{class_obj.name}_{current.date()}_{period}"
                        )
                        var_dict = {
                            "variable": var,
                            "name": class_obj.name,
                            "date": current,
                            "period": period,
                            "instructor": getattr(class_obj, "instructor", "default_instructor")
                        }
                        self.variables.append(var_dict)
                        
                        # Store key for potential forced assignments
                        key = (class_obj.name, current.date(), period)
                        self._forced_assignments[key] = var_dict
            current += timedelta(days=1)
            
        context = SchedulerContext(
            request=request,
            model=self.model,
            solver=self.solver,
            start_date=start,
            end_date=end
        )
        context.variables = self.variables
        return context
    
    def apply_constraint(self, constraint: BaseConstraint, context: SchedulerContext, enabled: bool = True) -> None:
        """
        Apply a constraint to the test context.
        
        Args:
            constraint: The constraint to test
            context: The scheduler context to apply it to
            enabled: Whether the constraint should be enabled
        """
        print(f"\nApplying constraint: {constraint.name} (enabled={enabled})")
        
        # Set the enabled state
        constraint.enabled = enabled
        
        # Add test data based on constraint type
        if constraint.name == "instructor_availability" and not enabled:
            # Add some availability data with unavailable periods
            date = context.start_date
            instructor = "default_instructor"
            if not context.request.instructorAvailability:
                avail = InstructorAvailability(
                    instructor=instructor,
                    date=date,
                    periods=[1, 2],  # Mark first two periods as unavailable
                    unavailableSlots=[],
                    preferredSlots=[],
                    avoidSlots=[]
                )
                context.request.instructorAvailability.append(avail)
                
        elif constraint.name == "conflict_periods" and not enabled:
            # Add conflict periods to first class
            if context.request.classes:
                class_obj = context.request.classes[0]
                if not hasattr(class_obj, "weeklySchedule"):
                    class_obj.weeklySchedule = WeeklySchedule()
                if not hasattr(class_obj.weeklySchedule, "conflicts"):
                    class_obj.weeklySchedule.conflicts = []
                    
                # Add conflict for first period on Mondays
                conflict = ConflictPeriod(dayOfWeek=1, period=1)  # Monday, period 1
                class_obj.weeklySchedule.conflicts.append(conflict)
                print(f"Added conflict period for {class_obj.name}: day={conflict.dayOfWeek}, period={conflict.period}")
                
        elif constraint.name == "required_periods" and not enabled:
            # Add required period for first class
            if context.request.classes:
                class_obj = context.request.classes[0]
                if not hasattr(class_obj, "weeklySchedule"):
                    class_obj.weeklySchedule = WeeklySchedule()
                if not hasattr(class_obj.weeklySchedule, "requiredPeriods"):
                    class_obj.weeklySchedule.requiredPeriods = []
                    
                # Find first Monday
                current = context.start_date
                while current.weekday() != 0:  # Monday = 0
                    current += timedelta(days=1)
                    
                # Configure first Monday and Tuesday with specific required periods
                required_periods = [
                    RequiredPeriod(
                        date=current.strftime("%Y-%m-%d"),
                        period=1  # First period on Monday
                    ),
                    RequiredPeriod(
                        date=(current + timedelta(days=1)).strftime("%Y-%m-%d"),
                        period=2  # Second period on Tuesday
                    )
                ]
                class_obj.weeklySchedule.requiredPeriods.extend(required_periods)
                for required in required_periods:
                    print(f"Added required period for {class_obj.name}: date={required.date}, period={required.period}")
        
        # Set default limits for limit constraints if not already set
        default_limits = {
            "daily_limit": ("maxClassesPerDay", 2),
            "weekly_limit": ("maxClassesPerWeek", 8),
            "minimum_periods": ("minPeriodsPerWeek", 5)
        }
        
        if constraint.name in default_limits:
            attr_name, default_value = default_limits[constraint.name]
            if not hasattr(context.request.constraints, attr_name):
                setattr(context.request.constraints, attr_name, default_value)
        
        # If disabled, force violating assignments
        if not enabled:
            print("Forcing violating assignments...")
            self._force_violating_assignments(constraint, context)
        else:
            print("Applying normal constraints...")
            constraint.apply(context)
    
    def _force_violating_assignments(self, constraint: BaseConstraint, context: SchedulerContext) -> None:
        """Force assignments that would violate the given constraint"""
        if constraint.name == "minimum_periods":
            # Force fewer classes than minimum required - be aggressive to ensure violation
            date = context.start_date
            # Always force exactly one assignment to ensure violation
            class_obj = context.request.classes[0]  # Use first class
            base_min = context.request.constraints.minPeriodsPerWeek

            print(f"Forcing single assignment for {class_obj.name}:")
            print(f"- Base minimum required: {base_min}")
            
            # Force exactly one assignment in first period
            first_period = 1
            key = (class_obj.name, date.date(), first_period)
            if key in self._forced_assignments:
                self.model.Add(self._forced_assignments[key]["variable"] == 1)
                print(f"- Forced assignment in period {first_period}")
                # Force all other periods to be 0
                for period in range(2, 9):
                    key = (class_obj.name, date.date(), period)
                    if key in self._forced_assignments:
                        self.model.Add(self._forced_assignments[key]["variable"] == 0)
                        print(f"- Forced zero for period {period}")
            print("Completed minimum periods violation setup")
                        
        elif constraint.name == "required_periods":
            # When checking required periods, force non-assignment to all required periods
            if context.request.classes:
                class_obj = context.request.classes[0]
                
                if hasattr(class_obj, "weeklySchedule") and class_obj.weeklySchedule.requiredPeriods:
                    print("Setting up required periods violation:")
                    
                    # First, force non-assignment to all required periods
                    for required in class_obj.weeklySchedule.requiredPeriods:
                        required_date = datetime.strptime(required.date, "%Y-%m-%d")
                        key = (class_obj.name, required_date.date(), required.period)
                        if key in self._forced_assignments:
                            print(f"- Forcing {class_obj.name} to skip required period on {required_date.date()} period {required.period}")
                            self.model.Add(self._forced_assignments[key]["variable"] == 0)

                    # Then force assignment to a non-required period to ensure we have something to validate
                    print("Setting up alternate assignment:")
                    first_required = class_obj.weeklySchedule.requiredPeriods[0]
                    required_date = datetime.strptime(first_required.date, "%Y-%m-%d")
                    non_required_period = 8  # Use last period of the day
                    alt_key = (class_obj.name, required_date.date(), non_required_period)
                    if alt_key in self._forced_assignments:
                        print(f"- Forcing alternate assignment to period {non_required_period}")
                        self.model.Add(self._forced_assignments[alt_key]["variable"] == 1)
                                
        elif constraint.name == "conflict_periods":
            # Force assignment during conflict period
            if context.request.classes:
                class_obj = context.request.classes[0]
                
                if hasattr(class_obj, "weeklySchedule") and class_obj.weeklySchedule.conflicts:
                    print("Setting up conflict periods violation:")
                    # Find first conflict period
                    conflict = class_obj.weeklySchedule.conflicts[0]
                    # Find first matching date
                    current = context.start_date
                    while current.weekday() + 1 != conflict.dayOfWeek:
                        current += timedelta(days=1)
                        
                    # First, ensure at least one forced assignment to create a conflict
                    key = (class_obj.name, current.date(), conflict.period)
                    if key in self._forced_assignments:
                        print(f"- Forcing {class_obj.name} into conflict period on {current.date()} period {conflict.period}")
                        self.model.Add(self._forced_assignments[key]["variable"] == 1)
                        
                    # Also force a non-conflict assignment to ensure we have multiple assignments
                    non_conflict_period = conflict.period + 1 if conflict.period < 8 else conflict.period - 1
                    alt_key = (class_obj.name, current.date(), non_conflict_period)
                    if alt_key in self._forced_assignments:
                        print(f"- Forcing additional assignment to non-conflict period {non_conflict_period}")
                        self.model.Add(self._forced_assignments[alt_key]["variable"] == 1)
                    
                    # Ensure other variables aren't assigned (to keep the test focused)
                    for var_key, var_dict in self._forced_assignments.items():
                        if var_key not in [key, alt_key]:
                            self.model.Add(var_dict["variable"] == 0)
                            
                    print("Completed conflict violation setup")
                        
        elif constraint.name == "no_overlap":
            # Force two classes to overlap in the same time slot
            if len(context.request.classes) >= 2:
                print("Setting up overlap violation:")
                date = context.start_date
                period = 1  # Use first period

                # Force first two classes into the same slot
                for idx in range(2):
                    class_obj = context.request.classes[idx]
                    key = (class_obj.name, date.date(), period)
                    if key in self._forced_assignments:
                        print(f"- Forcing {class_obj.name} into period {period} on {date.date()}")
                        self.model.Add(self._forced_assignments[key]["variable"] == 1)

                # Force all other periods to be empty
                for var_key, var_dict in self._forced_assignments.items():
                    name, slot_date, slot_period = var_key
                    if slot_date == date.date() and slot_period != period:
                        self.model.Add(var_dict["variable"] == 0)

                print("Completed overlap violation setup")

        elif constraint.name == "instructor_availability":
            # Force classes into unavailable periods
            if context.request.instructorAvailability and context.request.classes:
                avail = context.request.instructorAvailability[0]
                unavailable_periods = avail.periods  # These are the periods marked as unavailable
                
                # Schedule classes in unavailable periods
                for period in unavailable_periods:
                    class_obj = context.request.classes[0]  # Use first class
                    key = (class_obj.name, avail.date.date(), period)
                    if key in self._forced_assignments:
                        self.model.Add(self._forced_assignments[key]["variable"] == 1)
                        
        elif constraint.name == "consecutive_period":
            # Force consecutive periods for an instructor
            if len(context.request.classes) >= 1:
                date = context.start_date
                class_obj = context.request.classes[0]  # Use the same class for consecutive periods
                
                # Schedule class in consecutive periods (1 and 2)
                for period in [1, 2]:
                    key = (class_obj.name, date.date(), period)
                    if key in self._forced_assignments:
                        self.model.Add(self._forced_assignments[key]["variable"] == 1)
                        
        elif constraint.name == "instructor_load":
            # Force more classes than allowed per day for an instructor
            date = context.start_date
            max_per_day = getattr(constraint, "max_classes_per_day", 2)
            class_obj = context.request.classes[0]  # Use first class
            
            # Schedule more classes than allowed in one day
            for period in range(1, max_per_day + 3):  # Force 2 more than allowed
                key = (class_obj.name, date.date(), period)
                if key in self._forced_assignments:
                    self.model.Add(self._forced_assignments[key]["variable"] == 1)
                    
        elif constraint.name == "daily_limit":
            # Force more classes than allowed in one day
            date = context.start_date
            max_per_day = context.request.constraints.maxClassesPerDay
            class_obj = context.request.classes[0]  # Use first class
            
            # Force more assignments than allowed in one day
            for period in range(1, max_per_day + 3):  # Force 2 more than allowed
                key = (class_obj.name, date.date(), period)
                if key in self._forced_assignments:
                    self.model.Add(self._forced_assignments[key]["variable"] == 1)
                    
        elif constraint.name == "weekly_limit":
            # Force too many classes in one week
            max_per_week = context.request.constraints.maxClassesPerWeek
            class_obj = context.request.classes[0]  # Use first class
            
            # Schedule classes across days to exceed weekly limit 
            current = context.start_date
            assigned = 0
            days_used = 0
            
            while assigned < max_per_week + 2 and days_used < 5:  # Try to assign 2 more than limit
                if current.weekday() < 5:  # Weekdays only
                    # Try periods 1-3 on each day
                    for period in range(1, 4):
                        if assigned < max_per_week + 2:  # Still need more assignments
                            key = (class_obj.name, current.date(), period)
                            if key in self._forced_assignments:
                                self.model.Add(self._forced_assignments[key]["variable"] == 1)
                                assigned += 1
                    days_used += 1
                current += timedelta(days=1)
    
    def solve(self) -> bool:
        """
        Solve the model with applied constraints.
        Returns True if a solution was found.
        """
        print("\nSolving model...")
        status = self.solver.Solve(self.model)
        print(f"Solver status: {status}")
        print(f"- OPTIMAL: {status == cp_model.OPTIMAL}")
        print(f"- FEASIBLE: {status == cp_model.FEASIBLE}")
        print(f"- INFEASIBLE: {status == cp_model.INFEASIBLE}")
        
        is_solved = status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        if not is_solved:
            print("Failed to find feasible solution!")
        return is_solved
    
    def get_solution_assignments(self, context: SchedulerContext) -> List[Dict[str, Any]]:
        """
        Get assignments from the solved model.
        
        Args:
            context: The scheduler context with solved model
            
        Returns:
            List of assignments with class name, date, and period
        """
        assignments = []
        print("\nGetting solution assignments:")
        
        for var_dict in self.variables:
            var = var_dict["variable"]
            if self.solver.Value(var) == 1:
                assignment = {
                    "name": var_dict["name"],
                    "date": var_dict["date"],
                    "timeSlot": {"period": var_dict["period"]},
                    "instructor": var_dict.get("instructor")
                }
                assignments.append(assignment)
                print(f"- Found assignment: {var_dict['name']} on {var_dict['date'].date()} period {var_dict['period']}")
                
        return assignments
    
    def validate_constraint(
        self,
        constraint: BaseConstraint,
        context: SchedulerContext
    ) -> List[ConstraintViolation]:
        """
        Validate assignments against a constraint.
        
        Args:
            constraint: The constraint to validate
            context: The scheduler context with assignments
            
        Returns:
            List of any constraint violations found
        """
        print(f"\nValidating constraint: {constraint.name}")
        assignments = self.get_solution_assignments(context)
        violations = constraint.validate(assignments, context)
        print(f"Found {len(violations)} violations")
        if violations:
            for v in violations:
                print(f"- {v.message}")
        return violations

def create_test_harness() -> ConstraintTestHarness:
    """Factory function to create a fresh test harness"""
    return ConstraintTestHarness()
