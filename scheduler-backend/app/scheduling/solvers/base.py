from typing import List, Dict, Any, Optional
import traceback
import time
from datetime import datetime, timedelta

from ortools.sat.python import cp_model

from ..core import SchedulerContext
from ...models import (
    ScheduleRequest, 
    ScheduleResponse, 
    ScheduleAssignment, 
    TimeSlot,
    ScheduleMetadata,
    DistributionMetrics,
    WeeklyDistributionMetrics,
    DailyDistributionMetrics
)
from dateutil.tz import UTC

class BaseSolver:
    """Base solver implementation with common functionality"""
    
    def __init__(self, name: str):
        self.name = name
        self.constraints = []
        self.objectives = []
        
    def add_constraint(self, constraint: Any) -> None:
        """Add a constraint to the solver"""
        self.constraints.append(constraint)
        
    def add_objective(self, objective: Any) -> None:
        """Add an objective to the solver"""
        self.objectives.append(objective)
        
    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a schedule using the solver configuration"""
        print(f"\nStarting {self.name} solver for {len(request.classes)} classes...")
        print("\nSolver configuration:")
        print("Constraints:")
        for constraint in self.constraints:
            print(f"- {constraint.name}")
        print("\nObjectives:")
        for objective in self.objectives:
            print(f"- {objective.name} (weight: {objective.weight})")
            
        try:
            # Create solver and model
            model = cp_model.CpModel()
            solver = cp_model.CpSolver()
            
            # Configure solver parameters for timeout and performance
            solver.parameters.max_time_in_seconds = 120.0  # 2 minute timeout
            solver.parameters.log_search_progress = True
            solver.parameters.num_search_workers = 8
            
            # Parse dates
            start_date = datetime.fromisoformat(request.startDate)
            end_date = datetime.fromisoformat(request.endDate)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=UTC)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=UTC)
            
            # Create context
            context = SchedulerContext(
                model=model,
                solver=solver,
                request=request,
                start_date=start_date,
                end_date=end_date
            )
            
            # Create variables
            self._create_variables(context)
            print(f"\nCreated {len(context.variables)} schedule variables")
            
            # Log available slots per class
            print("\nAvailable slots per class:")
            by_class = {}
            for var in context.variables:
                class_name = var["name"]
                if class_name not in by_class:
                    by_class[class_name] = []
                by_class[class_name].append(var)
            
            for class_name, vars_list in by_class.items():
                print(f"\nClass {class_name}:")
                print(f"- Total available slots: {len(vars_list)}")
                # Get class's conflicts
                class_obj = next(c for c in request.classes if c.name == class_name)
                print(f"- Conflict periods: {len(class_obj.conflicts)}")
                # Group by day
                by_day = {}
                for var in vars_list:
                    day = var["date"].strftime("%Y-%m-%d")
                    if day not in by_day:
                        by_day[day] = []
                    by_day[day].append(var["period"])
                for day, periods in by_day.items():
                    print(f"  {day}: periods {sorted(periods)}")
            
            # Apply constraints
            for constraint in self.constraints:
                print(f"\nApplying constraint: {constraint.name}")
                constraint.apply(context)
            
            # Create objective function
            objective_terms = []
            for objective in self.objectives:
                print(f"\nAdding objective: {objective.name} (weight: {objective.weight})")
                terms = objective.create_terms(context)
                weighted_terms = [objective.weight * term for term in terms]
                objective_terms.extend(weighted_terms)
                
            if objective_terms:
                context.model.Maximize(sum(objective_terms))
            
            # Add search heuristics
            print("\nAdding search heuristics...")
            
            # Get all variables in a flat list
            all_vars = [var["variable"] for var in context.variables]
            
            # Count conflicts per class to identify most constrained classes
            conflicts_by_class = {}
            for class_obj in context.request.classes:
                conflicts_by_class[class_obj.name] = len(class_obj.conflicts)
            
            # Sort variables by number of conflicts (most constrained first)
            sorted_vars = sorted(
                context.variables,
                key=lambda v: (-conflicts_by_class[v["name"]], v["date"].toordinal(), v["period"])
            )
            sorted_var_list = [v["variable"] for v in sorted_vars]
            
            # Add decision strategy
            print("Adding decision strategy:")
            print("1. Try most constrained classes first")
            print("2. Try earlier dates before later dates")
            print("3. Try earlier periods before later periods")
            context.model.AddDecisionStrategy(
                sorted_var_list,
                cp_model.CHOOSE_FIRST,  # Try variables in the order we sorted them
                cp_model.SELECT_MIN_VALUE  # Try false (0) before true (1) to avoid unnecessary assignments
            )
            
            # Create solution callback to track best solution
            callback = SolutionCallback(context)
            
            # Solve with timeout
            print("\nStarting solver with 2 minute timeout...")
            start_time = time.time()
            status = solver.Solve(context.model, callback)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Check solution status and get best solution within time limit
            solution_found = False
            if status == cp_model.OPTIMAL:
                print("Found optimal solution!")
                solution_found = True
            elif status == cp_model.FEASIBLE:
                print("Found feasible solution within time limit")
                solution_found = True
            elif callback._solutions > 0:
                print("Time limit reached, using best solution found")
                solution_found = True
                status = cp_model.FEASIBLE  # Use best feasible solution found
            else:
                raise Exception("No solution found within time limit")
            
            # Convert solution to assignments using best solution found
            assignments = callback.get_best_solution()
            
            # Get distribution metrics if available
            distribution_metrics = None
            distribution_obj = next(
                (obj for obj in self.objectives if obj.__class__.__name__ == "DistributionObjective"),
                None
            )
            if distribution_obj and hasattr(distribution_obj, "calculate_metrics"):
                metrics = distribution_obj.calculate_metrics(assignments, context)
                
                # Convert classesPerWeek keys to strings
                classes_per_week_str = {str(k): v for k, v in metrics.classes_per_week.items()}
                
                distribution_metrics = DistributionMetrics(
                    weekly=WeeklyDistributionMetrics(
                        variance=metrics.week_variance,
                        classesPerWeek=classes_per_week_str,
                        score=-100 * metrics.week_variance  # Penalize variance
                    ),
                    daily={
                        date: DailyDistributionMetrics(
                            periodSpread=spread,
                            teacherLoadVariance=metrics.teacher_load_variance.get(date, 0.0),
                            classesByPeriod=dict(metrics.classes_per_period.get(date, {}))  # Already string keys
                        )
                        for date, spread in metrics.period_spread.items()
                    },
                    totalScore=metrics.distribution_score
                )
            
            # Create metadata using best objective value
            metadata = ScheduleMetadata(
                duration_ms=duration_ms,
                solutions_found=callback._solutions,
                score=int(callback._best_objective if objective_terms else 0),
                gap=float(
                    (callback._best_objective - solver.BestObjectiveBound()) / 
                    abs(callback._best_objective)
                    if callback._best_objective != 0
                    else 0.0
                )
            )
            
            print("\nSolution metrics:")
            print(f"- Duration: {metadata.duration_ms}ms")
            print(f"- Solutions found: {metadata.solutions_found}")
            print(f"- Score: {metadata.score}")
            print(f"- Gap: {metadata.gap:.2%}")
            
            # Validate constraints
            print("\nValidating constraints...")
            all_violations = []
            for constraint in self.constraints:
                violations = constraint.validate(assignments, context)
                if violations:
                    print(f"\nViolations for {constraint.name}:")
                    for v in violations:
                        print(f"- {v}")
                    all_violations.extend(violations)
            
            if all_violations:
                raise Exception(
                    f"Schedule validation failed with {len(all_violations)} violations"
                )
            
            print("\nAll constraints satisfied!")
            return ScheduleResponse(assignments=assignments, metadata=metadata)
            
        except Exception as e:
            print(f"Scheduling error in {self.name} solver: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            raise

    def _create_variables(self, context: SchedulerContext) -> None:
        """Create CP-SAT variables for each possible assignment"""
        print("\nCreating schedule variables...")
        
        # First count weekdays in range
        current_date = context.start_date
        weekdays = 0
        while current_date <= context.end_date:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                weekdays += 1
            current_date = current_date + timedelta(days=1)
        
        print(f"Schedule range: {context.start_date.date()} to {context.end_date.date()}")
        print(f"Available weekdays: {weekdays}")
        print(f"Total classes: {len(context.request.classes)}")
        print(f"Periods per day: 8")
        print(f"Maximum possible slots: {weekdays * 8}")
        
        # Create variables
        for class_obj in context.request.classes:
            print(f"\nCreating variables for class {class_obj.name}:")
            print(f"- Conflicts: {len(class_obj.conflicts)}")
            
            current_date = context.start_date
            class_vars = 0
            while current_date <= context.end_date:
                # Only create variables for weekdays and non-conflicting periods
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    weekday = current_date.weekday() + 1  # Convert to 1-5 for Monday-Friday
                    
                    # Get conflicts for this day
                    conflicts = {
                        conflict.period
                        for conflict in class_obj.conflicts
                        if conflict.dayOfWeek == weekday
                    }
                    
                    # Create variables only for non-conflicting periods
                    for period in range(1, 9):  # periods 1-8
                        if period not in conflicts:
                            var_name = f"class_{class_obj.name}_{current_date.date()}_{period}"
                            var = context.model.NewBoolVar(var_name)
                            context.variables.append({
                                "variable": var,
                                "name": class_obj.name,
                                "date": current_date,
                                "period": period
                            })
                            class_vars += 1
                current_date = current_date + timedelta(days=1)
            print(f"- Created {class_vars} variables")

class SolutionCallback(cp_model.CpSolverSolutionCallback):
    """Callback to track solver progress and store intermediate solutions"""
    
    def __init__(self, context: SchedulerContext):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._solutions = 0
        self._start_time = time.time()
        self._last_log_time = time.time()
        self._last_log_count = 0
        self._best_solution: Optional[List[ScheduleAssignment]] = None
        self._best_objective = float('-inf')
        self._context = context
        
    def on_solution_callback(self):
        """Called when solver finds a new solution"""
        self._solutions += 1
        current_time = time.time()
        
        # Track best solution
        objective_value = self.ObjectiveValue()
        if objective_value > self._best_objective:
            self._best_objective = objective_value
            self._best_solution = self._convert_solution()
            
            # Log solution details
            print(f"\nFound better solution {self._solutions} at {current_time - self._start_time:.1f}s")
            print(f"Objective value: {objective_value}")
            
            # Count assignments by day
            by_day = {}
            for assignment in self._best_solution:
                date = datetime.fromisoformat(assignment.date).date()
                if date not in by_day:
                    by_day[date] = []
                by_day[date].append(assignment)
            
            print("\nAssignments by day:")
            for date in sorted(by_day.keys()):
                assignments = by_day[date]
                print(f"{date}: {len(assignments)} classes")
                for assignment in sorted(assignments, key=lambda a: a.timeSlot.period):
                    print(f"  Period {assignment.timeSlot.period}: {assignment.name}")
        
        # Log every 3 seconds
        if (current_time - self._last_log_time) >= 3.0:
            elapsed = current_time - self._start_time
            solutions_since_last = self._solutions - self._last_log_count
            rate = solutions_since_last / (current_time - self._last_log_time)
            
            print(f"\nSearch status at {elapsed:.1f}s:")
            print(f"- Solutions found: {self._solutions} ({rate:.1f} solutions/sec)")
            print(f"- Best objective: {self.BestObjectiveBound()}")
            print(f"- Current objective: {objective_value}")
            if objective_value != 0:
                gap = (
                    (objective_value - self.BestObjectiveBound()) / 
                    abs(objective_value)
                )
                print(f"- Gap: {gap:.2%}")
            
            self._last_log_time = current_time
            self._last_log_count = self._solutions
            
    def _convert_solution(self) -> List[ScheduleAssignment]:
        """Convert current solution to schedule assignments"""
        assignments = []
        
        for var in self._context.variables:
            if self.BooleanValue(var["variable"]):
                assignments.append(
                    ScheduleAssignment(
                        name=var["name"],
                        date=var["date"].isoformat(),
                        timeSlot=TimeSlot(
                            dayOfWeek=var["date"].weekday() + 1,
                            period=var["period"]
                        )
                    )
                )
        
        return assignments
        
    def get_best_solution(self) -> List[ScheduleAssignment]:
        """Get the best solution found so far"""
        if not self._best_solution:
            return []  # No solution found
        return self._best_solution
