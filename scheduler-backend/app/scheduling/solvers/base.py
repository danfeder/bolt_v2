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
    DistributionMetrics
)
from dateutil import parser
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
            solver.parameters.max_time_in_seconds = 30.0  # 30 second timeout
            solver.parameters.log_search_progress = True
            solver.parameters.num_search_workers = 8
            
            # Parse dates
            start_date = parser.parse(request.startDate)
            end_date = parser.parse(request.endDate)
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
            print(f"Created {len(context.variables)} schedule variables")
            
            # Apply constraints
            for constraint in self.constraints:
                print(f"Applying constraint: {constraint.name}")
                constraint.apply(context)
            
            # Create objective function
            objective_terms = []
            for objective in self.objectives:
                print(f"Adding objective: {objective.name} (weight: {objective.weight})")
                terms = objective.create_terms(context)
                weighted_terms = [objective.weight * term for term in terms]
                objective_terms.extend(weighted_terms)
                
            if objective_terms:
                context.model.Maximize(sum(objective_terms))
            
            # Create solution callback to track best solution
            callback = SolutionCallback(context)
            
            # Solve with timeout
            print("\nStarting solver with 30 second timeout...")
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
                distribution_metrics = DistributionMetrics(
                    weekly={
                        "variance": metrics.week_variance,
                        "classesPerWeek": metrics.classes_per_week,
                        "score": -100 * metrics.week_variance  # Penalize variance
                    },
                    daily={
                        date: {
                            "periodSpread": spread,
                            "teacherLoadVariance": metrics.teacher_load_variance.get(date, 0.0),
                            "classesByPeriod": metrics.classes_per_period.get(date, {})
                        }
                        for date, spread in metrics.period_spread.items()
                    },
                    totalScore=metrics.distribution_score
                )
            
            # Create metadata using best objective value
            metadata = ScheduleMetadata(
                solver=self.name,
                duration=duration_ms,
                score=int(callback._best_objective if objective_terms else 0),
                status=str(status),
                solutions_found=callback._solutions,
                optimization_gap=(
                    (callback._best_objective - solver.BestObjectiveBound()) / 
                    abs(callback._best_objective)
                    if callback._best_objective != 0
                    else 0.0
                ),
                distribution=distribution_metrics
            )
            
            print("\nSolution metrics:")
            print(f"- Duration: {metadata.duration}ms")
            print(f"- Solutions found: {metadata.solutions_found}")
            print(f"- Score: {metadata.score}")
            print(f"- Gap: {metadata.optimization_gap:.2%}")
            
            # Validate constraints
            print("\nValidating constraints...")
            all_violations = []
            for constraint in self.constraints:
                violations = constraint.validate(assignments, context)
                if violations:
                    print(f"\nViolations for {constraint.name}:")
                    for v in violations:
                        print(f"- {v.message}")
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
        for class_obj in context.request.classes:
            current_date = context.start_date
            while current_date <= context.end_date:
                # Only create variables for weekdays
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    for period in range(1, 9):  # periods 1-8
                        var_name = f"class_{class_obj.id}_{current_date.date()}_{period}"
                        var = context.model.NewBoolVar(var_name)
                        context.variables.append({
                            "variable": var,
                            "classId": class_obj.id,
                            "date": current_date,
                            "period": period
                        })
                current_date = current_date + timedelta(days=1)

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
                        classId=var["classId"],
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
