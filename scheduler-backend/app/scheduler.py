from ortools.sat.python import cp_model
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import time
from dateutil import parser
from dateutil.tz import UTC
import traceback
from collections import defaultdict
import statistics
from typing import Dict, List, Tuple

from .models import (
    ScheduleRequest,
    ScheduleAssignment,
    ScheduleResponse,
    ScheduleMetadata,
    TimeSlot
)

class WeeklyDistribution:
    """Track and analyze class distribution across weeks"""
    def __init__(self):
        self.classes_per_week = defaultdict(int)
        
    def add_assignment(self, week_num: int):
        self.classes_per_week[week_num] += 1
        
    def get_variance(self) -> float:
        """Calculate variance in class counts across weeks"""
        if not self.classes_per_week:
            return 0.0
        counts = list(self.classes_per_week.values())
        return statistics.variance(counts) if len(counts) > 1 else 0.0
    
    def get_distribution_score(self) -> float:
        """Calculate distribution score (lower is better)"""
        variance = self.get_variance()
        return -100 * variance  # Penalize high variance
        
    def get_summary(self) -> Dict:
        """Get distribution summary for debug panel"""
        return {
            "classesPerWeek": dict(self.classes_per_week),
            "variance": self.get_variance(),
            "score": self.get_distribution_score()
        }

class DailyDistribution:
    """Track and analyze class distribution within days"""
    def __init__(self):
        self.classes_per_period = defaultdict(lambda: defaultdict(int))
        self.teacher_periods = defaultdict(lambda: defaultdict(int))
        
    def add_assignment(self, date: str, period: int, teacher_id: str):
        self.classes_per_period[date][period] += 1
        self.teacher_periods[date][teacher_id] += 1
        
    def get_period_spread(self, date: str) -> float:
        """Calculate how well classes are spread across periods (0-1)"""
        if date not in self.classes_per_period:
            return 1.0
        periods = self.classes_per_period[date]
        if not periods:
            return 1.0
        # Calculate variance in class counts across periods
        counts = [periods[p] for p in range(1, 9)]  # periods 1-8
        variance = statistics.variance(counts) if len(counts) > 1 else 0.0
        # Convert to spread score (1 - normalized variance)
        max_variance = 4.0  # Theoretical maximum for our case
        spread = 1.0 - min(variance / max_variance, 1.0)
        return spread
        
    def get_teacher_load_variance(self, date: str) -> float:
        """Calculate variance in teacher workload for a day"""
        if date not in self.teacher_periods:
            return 0.0
        loads = list(self.teacher_periods[date].values())
        return statistics.variance(loads) if len(loads) > 1 else 0.0
        
    def get_distribution_score(self) -> float:
        """Calculate overall distribution score (lower is better)"""
        total_score = 0
        for date in self.classes_per_period:
            # Penalize poor period spread
            spread_penalty = -200 * (1.0 - self.get_period_spread(date))
            # Penalize teacher load imbalance
            load_penalty = -150 * self.get_teacher_load_variance(date)
            total_score += spread_penalty + load_penalty
        return total_score
        
    def get_summary(self) -> Dict:
        """Get distribution summary for debug panel"""
        return {
            "byDate": {
                date: {
                    "periodSpread": self.get_period_spread(date),
                    "teacherLoadVariance": self.get_teacher_load_variance(date),
                    "classesByPeriod": dict(periods)
                }
                for date, periods in self.classes_per_period.items()
            },
            "score": self.get_distribution_score()
        }

def validate_schedule(assignments: List[ScheduleAssignment], request: ScheduleRequest) -> bool:
    """
    Validate that the schedule respects all constraints.
    Returns True if valid, False if any constraints are violated.
    """
    # Create lookup for assignments by day and period
    schedule_map = defaultdict(list)
    for assignment in assignments:
        date = parser.parse(assignment.date).date()
        key = (date, assignment.timeSlot.period)
        schedule_map[key].append(assignment)
        
        # Check teacher availability
        for teacher_avail in request.teacherAvailability:
            avail_date = parser.parse(teacher_avail.date).date()
            if date == avail_date:
                for unavailable in teacher_avail.unavailableSlots:
                    if (assignment.timeSlot.dayOfWeek == unavailable.dayOfWeek and 
                        assignment.timeSlot.period == unavailable.period):
                        print(f"Error: Class {assignment.classId} scheduled during teacher unavailable period: "
                              f"day {unavailable.dayOfWeek} period {unavailable.period}")
                        return False
    
    # Check each class's assignment against its conflicts and required periods
    for class_obj in request.classes:
        # Find this class's assignment
        class_assignments = [a for a in assignments if a.classId == class_obj.id]
        if len(class_assignments) != 1:
            print(f"Error: Class {class_obj.id} has {len(class_assignments)} assignments, should have exactly 1")
            return False
        
        assignment = class_assignments[0]
        weekday = parser.parse(assignment.date).weekday() + 1
        period = assignment.timeSlot.period
        
        # Check if assigned time conflicts with this class's conflicts
        for conflict in class_obj.weeklySchedule.conflicts:
            if conflict.dayOfWeek == weekday and conflict.period == period:
                print(f"Error: Class {class_obj.id} scheduled during conflict period: "
                      f"day {weekday} period {period}")
                return False
        
        # Check if class with required periods is scheduled in one of them
        if class_obj.weeklySchedule.requiredPeriods:
            is_required_period = any(
                rp.dayOfWeek == weekday and rp.period == period
                for rp in class_obj.weeklySchedule.requiredPeriods
            )
            if not is_required_period:
                print(f"Error: Class {class_obj.id} not scheduled in a required period")
                return False
        
        # Check for overlaps with other classes
        date = parser.parse(assignment.date).date()
        key = (date, period)
        if len(schedule_map[key]) > 1:
            print(f"Error: Multiple classes scheduled for {date} period {period}: "
                  f"{[a.classId for a in schedule_map[key]]}")
            return False
    
    print("Schedule validation passed!")
    print("\nDetailed schedule analysis:")
    
    # Print conflict, required period, and preference summary
    print("\nClass Schedule Requirements Summary:")
    for class_obj in request.classes:
        print(f"\n{class_obj.id}:")
        if class_obj.weeklySchedule.conflicts:
            print("  Conflicts:")
            for conflict in class_obj.weeklySchedule.conflicts:
                print(f"    - Day {conflict.dayOfWeek} Period {conflict.period}")
        else:
            print("  No conflicts")
            
        if class_obj.weeklySchedule.requiredPeriods:
            print("  Required Periods:")
            for required in class_obj.weeklySchedule.requiredPeriods:
                print(f"    - Day {required.dayOfWeek} Period {required.period}")
        else:
            print("  No required periods")
            
        if class_obj.weeklySchedule.preferredPeriods:
            print("  Preferred Periods (weight: {:.1f}):".format(
                class_obj.weeklySchedule.preferenceWeight))
            for preferred in class_obj.weeklySchedule.preferredPeriods:
                print(f"    - Day {preferred.dayOfWeek} Period {preferred.period}")
        else:
            print("  No preferred periods")
            
        if class_obj.weeklySchedule.avoidPeriods:
            print("  Avoid Periods (weight: {:.1f}):".format(
                class_obj.weeklySchedule.avoidanceWeight))
            for avoid in class_obj.weeklySchedule.avoidPeriods:
                print(f"    - Day {avoid.dayOfWeek} Period {avoid.period}")
        else:
            print("  No avoid periods")
    
    # Group assignments by date and week for limit validation
    assignments_by_date = defaultdict(list)
    assignments_by_week = defaultdict(list)
    start_date = parser.parse(request.startDate).date()
    
    for assignment in assignments:
        date = parser.parse(assignment.date).date()
        assignments_by_date[date].append(assignment)
        
        # Calculate week number
        week_num = (date - start_date).days // 7
        assignments_by_week[week_num].append(assignment)
    
    # Validate daily class limits
    for date, day_assignments in assignments_by_date.items():
        if len(day_assignments) > request.constraints.maxClassesPerDay:
            print(f"Error: {len(day_assignments)} classes scheduled on {date}, "
                  f"exceeds maximum of {request.constraints.maxClassesPerDay}")
            return False
    
    # Validate weekly class limits
    for week, week_assignments in assignments_by_week.items():
        if len(week_assignments) > request.constraints.maxClassesPerWeek:
            print(f"Error: {len(week_assignments)} classes scheduled in week {week}, "
                  f"exceeds maximum of {request.constraints.maxClassesPerWeek}")
            return False
        if len(week_assignments) < request.constraints.minPeriodsPerWeek:
            print(f"Error: Only {len(week_assignments)} classes scheduled in week {week}, "
                  f"below minimum of {request.constraints.minPeriodsPerWeek}")
            return False
    
    # Validate consecutive class constraints
    if request.constraints.consecutiveClassesRule == "hard":
        for date, day_assignments in assignments_by_date.items():
            # Sort assignments by period
            day_assignments.sort(key=lambda x: x.timeSlot.period)
            
            # Check for consecutive classes
            consecutive_count = 1
            for i in range(1, len(day_assignments)):
                if day_assignments[i].timeSlot.period == day_assignments[i-1].timeSlot.period + 1:
                    consecutive_count += 1
                    if consecutive_count > request.constraints.maxConsecutiveClasses:
                        print(f"Error: {consecutive_count} consecutive classes scheduled on {date}, "
                              f"exceeds maximum of {request.constraints.maxConsecutiveClasses}")
                        return False
                else:
                    consecutive_count = 1
    
    # Print schedule summary
    print("\nSchedule Summary:")
    for date in sorted(assignments_by_date.keys()):
        print(f"\n{date}:")
        day_assignments = sorted(assignments_by_date[date], 
                               key=lambda x: x.timeSlot.period)
        for assignment in day_assignments:
            print(f"  Period {assignment.timeSlot.period}: {assignment.classId}")
    
    # Print class limits summary
    print("\nClass Limits Summary:")
    print(f"Daily Limit ({request.constraints.maxClassesPerDay} max):")
    for date, day_assignments in sorted(assignments_by_date.items()):
        print(f"  {date}: {len(day_assignments)} classes")
    
    print(f"\nWeekly Limits (min {request.constraints.minPeriodsPerWeek}, "
          f"max {request.constraints.maxClassesPerWeek}):")
    for week, week_assignments in sorted(assignments_by_week.items()):
        print(f"  Week {week}: {len(week_assignments)} classes")
    
    print(f"\nConsecutive Classes (max {request.constraints.maxConsecutiveClasses}, "
          f"rule: {request.constraints.consecutiveClassesRule})")
    
    return True

def create_schedule_stable(request: ScheduleRequest) -> ScheduleResponse:
    """
    Stable version: Full scheduling with distribution optimization
    1) Each class is scheduled exactly once
    2) Only schedule on weekdays periods 1-8
    3) No overlapping classes in same period
    4) Respect conflict periods
    5) Classes with required periods must be scheduled in one of them
    6) Respect teacher availability
    7) Enforce daily and weekly class limits
    8) Handle consecutive class constraints
    9) Satisfy period preferences:
       - Maximize preferred period assignments (weighted)
       - Minimize avoided period assignments (weighted)
    10) Optimize distribution:
        - Even distribution across weeks
        - Even distribution within days
        - Balance teacher workload
    11) Prefer earlier dates (lowest priority)
    """
    start_time = time.time()
    
    try:
        # Create the model
        model = cp_model.CpModel()
        print(f"\nCreating schedule for {len(request.classes)} classes...")
        
        # Create variables for each possible assignment
        variables = create_schedule_variables(model, request)
        print(f"Created {len(variables)} schedule variables")
        
        # Add basic constraints
        add_single_assignment_constraints(model, variables, request)
        print("Added single assignment constraints")

        # Add no-overlap constraints
        add_no_overlap_constraints(model, variables, request)
        print("Added no-overlap constraints")

        # Add conflict constraints
        add_conflict_constraints(model, variables, request)
        print("Added conflict constraints")
        
        # Add teacher availability constraints
        add_teacher_availability_constraints(model, variables, request)
        print("Added teacher availability constraints")

        # Add required periods constraints
        add_required_periods_constraints(model, variables, request)
        print("Added required periods constraints")

        # Add class limit constraints
        add_daily_class_limits(model, variables, request)
        add_weekly_class_limits(model, variables, request)
        add_consecutive_class_constraints(model, variables, request)
        
        # Add objective: heavily reward required period assignments, penalize consecutive classes if soft constraint
        objective_terms = create_required_periods_objective(model, variables, request)
        
        # Add consecutive class penalties to objective if using soft constraints
        if request.constraints.consecutiveClassesRule == "soft":
            # Group variables by date and period
            by_date = {}
            for var in variables:
                date = var["date"].date()
                if date not in by_date:
                    by_date[date] = {}
                if var["period"] not in by_date[date]:
                    by_date[date][var["period"]] = []
                by_date[date][var["period"]].append(var)

            # Get all consecutive class penalty variables
            penalty_vars = []
            for date, periods in by_date.items():
                for period in range(1, 8):  # Check periods 1-7 (since we look at next period)
                    if period in periods and period + 1 in periods:
                        current_vars = [v["variable"] for v in periods[period]]
                        next_vars = [v["variable"] for v in periods[period + 1]]
                        
                        # Create penalty variables for consecutive classes
                        for curr in current_vars:
                            for next_var in next_vars:
                                penalty = model.NewBoolVar(f"consecutive_penalty_{date}_{period}")
                                # penalty is 1 if both periods are used
                                model.AddBoolAnd([curr, next_var]).OnlyEnforceIf(penalty)
                                penalty_vars.append(penalty)
            
            # Add penalties with lower weight than required periods
            for penalty_var in penalty_vars:
                objective_terms.append(-100 * penalty_var)  # Negative weight to penalize
        
        model.Maximize(sum(objective_terms))
        print("Added objective function with required periods priority and consecutive class penalties")
        
        # Solve
        solver = cp_model.CpSolver()
        print("\nStarting solver...")
        status = solver.Solve(model)
        print(f"Solver finished with status: {status}")
        
        if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
            raise Exception(f"No solution found. Solver status: {status}")
            
        # Convert solution to schedule
        assignments = convert_solution_to_assignments(solver, variables)
        print(f"Generated {len(assignments)} assignments")
        
        # Validate schedule
        print("\nValidating schedule...")
        if not validate_schedule(assignments, request):
            raise Exception("Schedule validation failed!")
        
        # Calculate score
        score = calculate_score_with_required_periods(assignments, request)
        print(f"\nSchedule score: {score}")
        
        return ScheduleResponse(
            assignments=assignments,
            metadata=ScheduleMetadata(
                solver="cp-sat-stable",
                duration=int((time.time() - start_time) * 1000),  # ms
                score=score
            )
        )
        
    except Exception as e:
        print(f"Scheduling error: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        raise

def add_daily_class_limits(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Add constraints for maximum classes per day"""
    # Group variables by date
    by_date = {}
    for var in variables:
        date = var["date"].date()
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(var["variable"])
    
    # For each date, ensure total classes doesn't exceed daily limit
    for date, vars_list in by_date.items():
        model.Add(sum(vars_list) <= request.constraints.maxClassesPerDay)
    
    print(f"Added daily class limit constraints (max {request.constraints.maxClassesPerDay} per day)")

def add_weekly_class_limits(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Add constraints for weekly class limits"""
    # Group variables by week
    by_week = {}
    for var in variables:
        # Get week number relative to start date
        start_date = parser.parse(request.startDate)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        week_num = (var["date"] - start_date).days // 7
        
        if week_num not in by_week:
            by_week[week_num] = []
        by_week[week_num].append(var["variable"])
    
    # For each week, ensure total classes is within limits
    for week, vars_list in by_week.items():
        # Maximum classes per week
        model.Add(sum(vars_list) <= request.constraints.maxClassesPerWeek)
        # Minimum periods per week
        model.Add(sum(vars_list) >= request.constraints.minPeriodsPerWeek)
    
    print(f"Added weekly class limit constraints (min {request.constraints.minPeriodsPerWeek}, max {request.constraints.maxClassesPerWeek} per week)")

def add_consecutive_class_constraints(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Add constraints for consecutive classes"""
    # Group variables by date
    by_date = {}
    for var in variables:
        date = var["date"].date()
        if date not in by_date:
            by_date[date] = {}
        if var["period"] not in by_date[date]:
            by_date[date][var["period"]] = []
        by_date[date][var["period"]].append(var)
    
    # For each date, check consecutive periods
    for date, periods in by_date.items():
        for period in range(1, 8):  # Check periods 1-7 (since we look at next period)
            if period in periods and period + 1 in periods:
                current_vars = [v["variable"] for v in periods[period]]
                next_vars = [v["variable"] for v in periods[period + 1]]
                
                if request.constraints.consecutiveClassesRule == "hard":
                    # Hard constraint: Cannot exceed max consecutive classes
                    if request.constraints.maxConsecutiveClasses == 1:
                        # If one class is scheduled, the next period must be empty
                        for curr in current_vars:
                            for next_var in next_vars:
                                model.Add(curr + next_var <= 1)
                else:
                    # Soft constraint: Penalize consecutive classes in objective
                    for curr in current_vars:
                        for next_var in next_vars:
                            penalty = model.NewBoolVar(f"consecutive_penalty_{date}_{period}")
                            # penalty is 1 if both periods are used
                            model.AddBoolAnd([curr, next_var]).OnlyEnforceIf(penalty)
    
    print(f"Added consecutive class constraints (max {request.constraints.maxConsecutiveClasses}, rule: {request.constraints.consecutiveClassesRule})")

def create_schedule_dev(request: ScheduleRequest) -> ScheduleResponse:
    """
    Development version: Adding distribution optimization
    1) Each class is scheduled exactly once
    2) Only schedule on weekdays periods 1-8
    3) No overlapping classes in same period
    4) Respect conflict periods
    5) Classes with required periods must be scheduled in one of them
    6) Respect teacher availability
    7) Enforce daily and weekly class limits
    8) Handle consecutive class constraints
    9) Satisfy period preferences:
       - Maximize preferred period assignments (weighted)
       - Minimize avoided period assignments (weighted)
    10) Optimize distribution:
        - Even distribution across weeks
        - Even distribution within days
        - Balance teacher workload
    11) Prefer earlier dates (lowest priority)
    """
    start_time = time.time()
    
    try:
        # Create the model
        model = cp_model.CpModel()
        print(f"\nCreating schedule for {len(request.classes)} classes...")
        
        # Create variables for each possible assignment
        variables = create_schedule_variables(model, request)
        print(f"Created {len(variables)} schedule variables")
        
        # Add basic constraints
        add_single_assignment_constraints(model, variables, request)
        print("Added single assignment constraints")

        # Add no-overlap constraints
        add_no_overlap_constraints(model, variables, request)
        print("Added no-overlap constraints")

        # Add conflict constraints
        add_conflict_constraints(model, variables, request)
        print("Added conflict constraints")
        
        # Add teacher availability constraints
        add_teacher_availability_constraints(model, variables, request)
        print("Added teacher availability constraints")

        # Add required periods constraints
        add_required_periods_constraints(model, variables, request)
        print("Added required periods constraints")

        # Add class limit constraints
        add_daily_class_limits(model, variables, request)
        add_weekly_class_limits(model, variables, request)
        add_consecutive_class_constraints(model, variables, request)
        
        # Initialize distribution trackers
        weekly_dist = WeeklyDistribution()
        daily_dist = DailyDistribution()
        
        # Add objective terms for required periods and preferences
        objective_terms = create_required_periods_objective(model, variables, request)
        
        # Add distribution optimization terms
        distribution_terms = create_distribution_objective(model, variables, request)
        objective_terms.extend(distribution_terms)
        
        # Add consecutive class penalties to objective if using soft constraints
        if request.constraints.consecutiveClassesRule == "soft":
            # Group variables by date and period
            by_date = {}
            for var in variables:
                date = var["date"].date()
                if date not in by_date:
                    by_date[date] = {}
                if var["period"] not in by_date[date]:
                    by_date[date][var["period"]] = []
                by_date[date][var["period"]].append(var)

            # Get all consecutive class penalty variables
            penalty_vars = []
            for date, periods in by_date.items():
                for period in range(1, 8):  # Check periods 1-7 (since we look at next period)
                    if period in periods and period + 1 in periods:
                        current_vars = [v["variable"] for v in periods[period]]
                        next_vars = [v["variable"] for v in periods[period + 1]]
                        
                        # Create penalty variables for consecutive classes
                        for curr in current_vars:
                            for next_var in next_vars:
                                penalty = model.NewBoolVar(f"consecutive_penalty_{date}_{period}")
                                # penalty is 1 if both periods are used
                                model.AddBoolAnd([curr, next_var]).OnlyEnforceIf(penalty)
                                penalty_vars.append(penalty)
            
            # Add penalties with lower weight than required periods
            for penalty_var in penalty_vars:
                objective_terms.append(-100 * penalty_var)  # Negative weight to penalize
        
        model.Maximize(sum(objective_terms))
        print("Added objective function with required periods priority and consecutive class penalties")
        
        # Solve
        solver = cp_model.CpSolver()
        print("\nStarting solver...")
        status = solver.Solve(model)
        print(f"Solver finished with status: {status}")
        
        if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
            raise Exception(f"No solution found. Solver status: {status}")
            
        # Convert solution to schedule
        assignments = convert_solution_to_assignments(solver, variables)
        print(f"Generated {len(assignments)} assignments")
        
        # Validate schedule
        print("\nValidating schedule...")
        if not validate_schedule(assignments, request):
            raise Exception("Schedule validation failed!")
        
        # Calculate scores and distribution metrics
        score = calculate_score_with_required_periods(assignments, request)
        
        # Track distribution metrics
        start_date = parser.parse(request.startDate)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
            
        for assignment in assignments:
            date = parser.parse(assignment.date)
            if date.tzinfo is None:
                date = date.replace(tzinfo=UTC)
            
            # Track weekly distribution
            week_num = (date - start_date).days // 7
            weekly_dist.add_assignment(week_num)
            
            # Track daily distribution
            class_obj = next(c for c in request.classes if c.id == assignment.classId)
            daily_dist.add_assignment(
                date.date().isoformat(),
                assignment.timeSlot.period,
                class_obj.id  # Using class ID as teacher ID for now
            )
        
        # Get distribution summaries
        weekly_summary = weekly_dist.get_summary()
        daily_summary = daily_dist.get_summary()
        
        print(f"\nSchedule Score: {score}")
        print("\nDistribution Summary:")
        print(f"Weekly variance: {weekly_summary['variance']:.2f}")
        print(f"Distribution score: {weekly_summary['score'] + daily_summary['score']}")
        
        return ScheduleResponse(
            assignments=assignments,
            metadata=ScheduleMetadata(
                solver="cp-sat-dev",
                duration=int((time.time() - start_time) * 1000),  # ms
                score=score,
                distribution={
                    "weekly": weekly_summary,
                    "daily": daily_summary,
                    "totalScore": weekly_summary['score'] + daily_summary['score']
                }
            )
        )
        
    except Exception as e:
        print(f"Scheduling error: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        raise

def add_required_periods_constraints(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Add constraints for required periods"""
    required_count = 0
    
    # First, identify classes that share required periods
    required_period_map = {}  # (dayOfWeek, period) -> [classIds]
    for class_obj in request.classes:
        if not class_obj.weeklySchedule.requiredPeriods:
            continue
        for rp in class_obj.weeklySchedule.requiredPeriods:
            key = (rp.dayOfWeek, rp.period)
            if key not in required_period_map:
                required_period_map[key] = []
            required_period_map[key].append(class_obj.id)
    
    # Print required period conflicts for debugging
    for (day, period), class_ids in required_period_map.items():
        if len(class_ids) > 1:
            print(f"Warning: Multiple classes require day {day} period {period}: {class_ids}")
    
    # Group variables by week
    by_week = {}  # week_num -> [(var, weekday, period)]
    start_date = parser.parse(request.startDate)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    
    for var in variables:
        week_num = (var["date"] - start_date).days // 7
        if week_num not in by_week:
            by_week[week_num] = []
        weekday = var["date"].weekday() + 1
        period = var["period"]
        by_week[week_num].append((var, weekday, period))
    
    for class_obj in request.classes:
        if not class_obj.weeklySchedule.requiredPeriods:
            continue
            
        # Get all variables for this class
        class_vars = [
            var for var in variables 
            if var["classId"] == class_obj.id
        ]
        
        # Create list of variables that represent required periods
        required_vars = []
        for week_num, week_vars in by_week.items():
            # Find all variables for this class in this week that match required periods
            week_required_vars = []
            for var, weekday, period in week_vars:
                if var["classId"] != class_obj.id:
                    continue
                    
                # Check if this time slot is a required period
                is_required = any(
                    rp.dayOfWeek == weekday and rp.period == period
                    for rp in class_obj.weeklySchedule.requiredPeriods
                )
                
                if is_required:
                    week_required_vars.append(var["variable"])
            
            # If we found any required periods in this week, add them to the list
            if week_required_vars:
                required_vars.extend(week_required_vars)
        
        if not required_vars:
            raise Exception(
                f"No valid time slots found for required periods of class {class_obj.id}. "
                f"Required periods: {[(rp.dayOfWeek, rp.period) for rp in class_obj.weeklySchedule.requiredPeriods]}\n"
                f"Available dates: {[var['date'].strftime('%Y-%m-%d') for var in class_vars]}\n"
                "Consider adding more weeks to the schedule range or checking teacher availability."
            )
        
        # Class must be scheduled in one of its required periods
        model.Add(sum(required_vars) == 1)
        required_count += 1
    
    print(f"Added required period constraints for {required_count} classes")

def create_required_periods_objective(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
) -> List[cp_model.IntVar]:
    """Create objective terms prioritizing required periods and preferences"""
    start_date = parser.parse(request.startDate)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
        
    terms = []
    
    for var in variables:
        # Get class object for this variable
        class_obj = next(c for c in request.classes if c.id == var["classId"])
        weekday = var["date"].weekday() + 1
        period = var["period"]
        
        # Check if this is a required period for this class
        is_required = any(
            rp.dayOfWeek == weekday and rp.period == period
            for rp in class_obj.weeklySchedule.requiredPeriods
        )
        
        if is_required:
            # Large reward for scheduling in required period (highest priority)
            terms.append(10000 * var["variable"])
        
        # Check if this is a preferred period
        is_preferred = any(
            pp.dayOfWeek == weekday and pp.period == period
            for pp in class_obj.weeklySchedule.preferredPeriods
        )
        
        if is_preferred:
            # Reward for preferred periods (weighted by class preference)
            weight = int(1000 * class_obj.weeklySchedule.preferenceWeight)
            terms.append(weight * var["variable"])
            
        # Check if this is an avoid period
        is_avoided = any(
            ap.dayOfWeek == weekday and ap.period == period
            for ap in class_obj.weeklySchedule.avoidPeriods
        )
        
        if is_avoided:
            # Penalty for avoided periods (weighted by class avoidance)
            weight = int(-500 * class_obj.weeklySchedule.avoidanceWeight)
            terms.append(weight * var["variable"])
        
        # Small reward for earlier dates (lowest priority)
        days_from_start = (var["date"] - start_date).days
        date_weight = 10 - days_from_start * 0.1
        terms.append(date_weight * var["variable"])
    
    return terms

def calculate_score_with_required_periods(
    assignments: List[ScheduleAssignment],
    request: ScheduleRequest
) -> int:
    """Calculate score including required period bonuses, preferences, and penalties"""
    score = 0
    start_date = parser.parse(request.startDate)
    
    # Ensure timezone-aware comparison
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    
    # Group assignments by date for consecutive class checking
    assignments_by_date = defaultdict(list)
    for assignment in assignments:
        date = parser.parse(assignment.date).date()
        assignments_by_date[date].append(assignment)
    
    # Track preference satisfaction for reporting
    total_preferred = 0
    total_avoided = 0
    
    for assignment in assignments:
        # Base score for valid assignment
        score += 10
        
        # Get class object
        class_obj = next(c for c in request.classes if c.id == assignment.classId)
        
        # Check if this is a required period
        is_required = any(
            rp.dayOfWeek == assignment.timeSlot.dayOfWeek and 
            rp.period == assignment.timeSlot.period
            for rp in class_obj.weeklySchedule.requiredPeriods
        )
        
        if is_required:
            # Large bonus for required period assignment (highest priority)
            score += 10000
            
        # Check if this is a preferred period
        is_preferred = any(
            pp.dayOfWeek == assignment.timeSlot.dayOfWeek and 
            pp.period == assignment.timeSlot.period
            for pp in class_obj.weeklySchedule.preferredPeriods
        )
        
        if is_preferred:
            # Bonus for preferred period (weighted by class preference)
            weight = int(1000 * class_obj.weeklySchedule.preferenceWeight)
            score += weight
            total_preferred += 1
            
        # Check if this is an avoid period
        is_avoided = any(
            ap.dayOfWeek == assignment.timeSlot.dayOfWeek and 
            ap.period == assignment.timeSlot.period
            for ap in class_obj.weeklySchedule.avoidPeriods
        )
        
        if is_avoided:
            # Penalty for avoided period (weighted by class avoidance)
            weight = int(-500 * class_obj.weeklySchedule.avoidanceWeight)
            score += weight
            total_avoided += 1
        
        # Small penalty for later dates
        date = parser.parse(assignment.date)
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        days_from_start = (date - start_date).days
        score -= days_from_start
    
    # Add penalties for consecutive classes if using soft constraints
    if request.constraints.consecutiveClassesRule == "soft":
        for date, day_assignments in assignments_by_date.items():
            # Sort assignments by period
            day_assignments.sort(key=lambda x: x.timeSlot.period)
            
            # Check for consecutive classes
            consecutive_count = 1
            for i in range(1, len(day_assignments)):
                if day_assignments[i].timeSlot.period == day_assignments[i-1].timeSlot.period + 1:
                    consecutive_count += 1
                    if consecutive_count > request.constraints.maxConsecutiveClasses:
                        # Apply penalty for each consecutive class beyond the limit
                        score -= 100  # Same penalty weight as in objective function
                else:
                    consecutive_count = 1
    
    # Print preference satisfaction summary
    print("\nPreference Satisfaction Summary:")
    print(f"Preferred periods satisfied: {total_preferred}")
    print(f"Avoided periods used: {total_avoided}")
    
    return score

def create_schedule_variables(
    model: cp_model.CpModel,
    request: ScheduleRequest
) -> List[Dict]:
    """Create boolean variables for each valid timeslot"""
    variables = []
    start_date = parser.parse(request.startDate)
    end_date = parser.parse(request.endDate)
    
    # Normalize to UTC for consistent date handling
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=UTC)
    
    current_date = start_date
    while current_date <= end_date:
        # Only create variables for weekdays (1-5)
        if current_date.weekday() < 5:
            for class_obj in request.classes:
                for period in range(1, 9):  # periods 1-8
                    var_name = f"class_{class_obj.id}_{current_date.date()}_{period}"
                    variables.append({
                        "variable": model.NewBoolVar(var_name),
                        "classId": class_obj.id,
                        "date": current_date,
                        "period": period
                    })
        current_date += timedelta(days=1)
    
    return variables

def add_single_assignment_constraints(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Each class must be scheduled exactly once"""
    for class_obj in request.classes:
        class_vars = [
            var["variable"] 
            for var in variables 
            if var["classId"] == class_obj.id
        ]
        model.Add(sum(class_vars) == 1)

def add_no_overlap_constraints(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """No two classes can be scheduled in the same period on the same day"""
    # Group variables by date and period
    by_date_period = {}
    for var in variables:
        key = (var["date"].date(), var["period"])
        if key not in by_date_period:
            by_date_period[key] = []
        by_date_period[key].append(var["variable"])
    
    # For each date and period, ensure at most one class is scheduled
    for vars_list in by_date_period.values():
        if len(vars_list) > 1:  # Only need constraint if multiple classes could be scheduled
            model.Add(sum(vars_list) <= 1)

def add_teacher_availability_constraints(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Don't schedule classes during teacher unavailable periods"""
    unavailable_count = 0
    
    # Print teacher availability data for debugging
    print("\nTeacher Availability Data:")
    for teacher_avail in request.teacherAvailability:
        avail_date = parser.parse(teacher_avail.date)
        if avail_date.tzinfo is None:
            avail_date = avail_date.replace(tzinfo=UTC)
        print(f"\nDate: {avail_date.date()}")
        print("Unavailable slots:")
        for slot in teacher_avail.unavailableSlots:
            print(f"  Day {slot.dayOfWeek} Period {slot.period}")
    
    # Convert teacher availability dates to weekdays
    teacher_unavailable = {}  # (date, period) -> bool
    for teacher_avail in request.teacherAvailability:
        avail_date = parser.parse(teacher_avail.date)
        if avail_date.tzinfo is None:
            avail_date = avail_date.replace(tzinfo=UTC)
        
        for unavailable in teacher_avail.unavailableSlots:
            key = (avail_date.date(), unavailable.period)
            teacher_unavailable[key] = True
            print(f"Added unavailable slot: {key}")
    
    # Add constraints for each variable
    for var in variables:
        date = var["date"]
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        period = var["period"]
        
        # Check if this timeslot is unavailable
        key = (date.date(), period)
        if key in teacher_unavailable:
            # If it's an unavailable period, this variable must be 0
            model.Add(var["variable"] == 0)
            unavailable_count += 1
            print(f"Added constraint for unavailable slot: {key}")
    
    print(f"Added {unavailable_count} teacher availability constraints")

def add_conflict_constraints(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
):
    """Don't schedule classes during their conflict periods"""
    conflict_count = 0
    for class_obj in request.classes:
        # Get all variables for this class
        class_vars = [
            var for var in variables 
            if var["classId"] == class_obj.id
        ]
        
        # For each variable, check if it conflicts with the weekly schedule
        for var in class_vars:
            # Get the weekday (1-5) and period for this variable
            weekday = var["date"].weekday() + 1
            period = var["period"]
            
            # Check if this time slot conflicts with the weekly schedule
            for conflict in class_obj.weeklySchedule.conflicts:
                if conflict.dayOfWeek == weekday and conflict.period == period:
                    # If it's a conflict period, this variable must be 0
                    model.Add(var["variable"] == 0)
                    conflict_count += 1
    
    print(f"Added {conflict_count} conflict constraints")

def create_distribution_objective(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
) -> List[cp_model.IntVar]:
    """Create objective terms for optimizing schedule distribution"""
    start_date = parser.parse(request.startDate)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
        
    terms = []
    
    # Group variables by week
    by_week = defaultdict(list)
    for var in variables:
        week_num = (var["date"] - start_date).days // 7
        by_week[week_num].append(var)
    
    # Create weekly distribution terms
    total_classes = len(request.classes)
    total_weeks = len(by_week)
    # Scale up by 100 to handle decimals as integers
    target_per_week = (total_classes * 100) // total_weeks
    for week_vars in by_week.values():
        # Sum of assignments for this week (scaled up)
        week_sum = sum(100 * var["variable"] for var in week_vars)
        # Penalize deviation from target
        deviation = model.NewIntVar(-1000, 1000, "week_deviation")
        model.Add(deviation == week_sum - target_per_week)
        # Use linear penalty instead of quadratic
        penalty = model.NewIntVar(-750000, 0, "week_penalty")
        # Absolute value of deviation using two constraints
        model.Add(penalty <= -750 * deviation)
        model.Add(penalty <= 750 * deviation)
        terms.append(penalty)
    
    # Group variables by date and period
    by_date = defaultdict(lambda: defaultdict(list))
    for var in variables:
        date = var["date"].date()
        period = var["period"]
        by_date[date][period].append(var)
    
    # Create daily distribution terms
    for date, periods in by_date.items():
        # Track assignments per period
        period_sums = []
        for period in range(1, 9):
            if period in periods:
                period_sum = sum(var["variable"] for var in periods[period])
                period_sums.append(period_sum)
        
        # Penalize uneven distribution across periods
        if period_sums:
            # Instead of calculating target, penalize differences between periods directly
            for i in range(len(period_sums)):
                for j in range(i + 1, len(period_sums)):
                    # Create deviation variable for each pair of periods
                    deviation = model.NewIntVar(-10, 10, f"period_diff_{date}_{i}_{j}")
                    model.Add(deviation == period_sums[i] - period_sums[j])
                    # Penalize differences between periods
                    penalty = model.NewIntVar(-500, 0, f"period_penalty_{date}_{i}_{j}")
                    # Absolute value of deviation using two constraints
                    model.Add(penalty <= -50 * deviation)
                    model.Add(penalty <= 50 * deviation)
                    terms.append(penalty)
    
    # Group variables by teacher (using class ID as proxy)
    by_teacher = defaultdict(lambda: defaultdict(list))
    for var in variables:
        date = var["date"].date()
        by_teacher[var["classId"]][date].append(var)
    
    # Create teacher workload distribution terms
    for teacher_vars in by_teacher.values():
        for date, day_vars in teacher_vars.items():
            # Sum of assignments for this teacher on this day
            day_sum = sum(var["variable"] for var in day_vars)
            # Create penalty that increases with number of classes
            penalty = model.NewIntVar(-1000, 0, f"teacher_penalty_{date}")
            # Penalize based on number of classes (more classes = bigger penalty)
            model.Add(penalty == -250 * day_sum)
            terms.append(penalty)
    
    return terms

def create_objective_terms(
    model: cp_model.CpModel,
    variables: List[Dict],
    request: ScheduleRequest
) -> List[cp_model.IntVar]:
    """Create terms for the objective function to optimize"""
    start_date = parser.parse(request.startDate)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
        
    terms = []
    
    for var in variables:
        # Calculate days from start
        days_from_start = (var["date"] - start_date).days
        
        # Create a weight that decreases with days from start
        # Weight = 1000 - (days × 10) so earlier dates are strongly preferred
        weight = 1000 - (days_from_start * 10)
        terms.append(weight * var["variable"])
        
        # Small bonus for using lower periods (spreading throughout the day)
        period_weight = 8 - var["period"]  # 7 for period 1, 0 for period 8
        terms.append(period_weight * var["variable"])
    
    return terms

def convert_solution_to_assignments(
    solver: cp_model.CpSolver,
    variables: List[Dict]
) -> List[ScheduleAssignment]:
    """Convert CP-SAT solution to schedule assignments"""
    assignments = []
    
    for var in variables:
        if solver.BooleanValue(var["variable"]):
            assignments.append(
                ScheduleAssignment(
                    classId=var["classId"],
                    date=var["date"].isoformat(),
                    timeSlot=TimeSlot(
                        dayOfWeek=var["date"].weekday() + 1,  # 1-5
                        period=var["period"]
                    )
                )
            )
    
    return assignments

def calculate_basic_score(
    assignments: List[ScheduleAssignment],
    request: ScheduleRequest
) -> int:
    """Calculate basic score: reward assignments, penalize later dates"""
    score = 0
    start_date = parser.parse(request.startDate)
    
    # Ensure timezone-aware comparison
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    
    for assignment in assignments:
        score += 10  # Base score for valid assignment
        date = parser.parse(assignment.date)
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        days_from_start = (date - start_date).days
        score -= days_from_start  # Penalize later dates
        
    return score
