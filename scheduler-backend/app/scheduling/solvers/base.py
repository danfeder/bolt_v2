from datetime import datetime, timedelta
from typing import List, Dict, Any
from dateutil import parser
from dateutil.tz import UTC
import time

from ortools.sat.python import cp_model

from ..core import (
    SchedulerBase,
    SchedulerContext,
    SchedulerMetrics,
    SolverCallback
)
from ...models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleAssignment,
    ScheduleMetadata,
    TimeSlot
)

class BaseSolver(SchedulerBase):
    """Base solver implementation with common functionality"""
    
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    
    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a schedule using the CP-SAT solver"""
        start_time = time.time()
        
        try:
            # Create model and context
            model = cp_model.CpModel()
            solver = cp_model.CpSolver()
            
            # Parse dates
            start_date = parser.parse(request.startDate)
            end_date = parser.parse(request.endDate)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=UTC)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=UTC)
                
            context = SchedulerContext(
                model=model,
                solver=solver,
                request=request,
                start_date=start_date,
                end_date=end_date
            )
            
            # Create schedule variables
            self._create_variables(context)
            print(f"Created {len(context.variables)} schedule variables")
            
            # Apply all constraints
            for constraint in self.constraints:
                print(f"Applying constraint: {constraint.name}")
                constraint.apply(context)
            
            # Create objective function
            objective_terms = []
            for objective in self.objectives:
                print(f"Adding objective: {objective.name} (weight: {objective.weight})")
                terms = objective.create_terms(context)
                # Scale terms by objective weight
                weighted_terms = [objective.weight * term for term in terms]
                objective_terms.extend(weighted_terms)
            
            if objective_terms:
                context.model.Maximize(sum(objective_terms))
            
            # Configure solver
            solver.parameters.log_search_progress = True
            solver.parameters.num_search_workers = 8
            solver.parameters.max_time_in_seconds = 300.0
            
            # Create callback
            callback = SolverCallback()
            
            # Solve
            print("\nStarting solver...")
            status = solver.Solve(context.model, callback)
            
            if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
                raise Exception(f"No solution found. Solver status: {status}")
            
            # Convert solution to assignments
            assignments = self._convert_solution(context)
            
            # Calculate metrics
            metrics = SchedulerMetrics(
                duration_ms=int((time.time() - start_time) * 1000),
                score=solver.ObjectiveValue(),
                distribution_score=context.debug_info.get("distribution_score", 0.0),
                solver_status=str(status),
                solutions_found=callback._solutions,
                optimization_gap=(
                    (solver.ObjectiveValue() - solver.BestObjectiveBound())
                    / abs(solver.ObjectiveValue())
                    if solver.ObjectiveValue() != 0
                    else 0.0
                )
            )
            
            return ScheduleResponse(
                assignments=assignments,
                metadata=ScheduleMetadata(
                    solver=self.name,
                    duration=metrics.duration_ms,
                    score=metrics.score,
                    distribution=context.debug_info.get("distribution", {})
                )
            )
            
        except Exception as e:
            print(f"Scheduling error: {str(e)}")
            raise
    
    def _create_variables(self, context: SchedulerContext) -> None:
        """Create CP-SAT variables for each possible assignment"""
        current_date = context.start_date
        
        while current_date <= context.end_date:
            # Only create variables for weekdays
            if current_date.weekday() < 5:
                for class_obj in context.request.classes:
                    for period in range(1, 9):  # periods 1-8
                        var_name = f"class_{class_obj.id}_{current_date.date()}_{period}"
                        context.variables.append({
                            "variable": context.model.NewBoolVar(var_name),
                            "classId": class_obj.id,
                            "date": current_date,
                            "period": period
                        })
            current_date += timedelta(days=1)
    
    def _convert_solution(
        self,
        context: SchedulerContext
    ) -> List[ScheduleAssignment]:
        """Convert CP-SAT solution to schedule assignments"""
        assignments = []
        
        for var in context.variables:
            if context.solver.BooleanValue(var["variable"]):
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
