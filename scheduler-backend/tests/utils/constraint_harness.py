from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ortools.sat.python import cp_model

from app.scheduling.core import SchedulerContext
from app.scheduling.constraints.base import BaseConstraint, ConstraintViolation
from app.models import ScheduleRequest
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
            request = ScheduleRequestGenerator.create_request(
                num_classes=num_classes,
                num_weeks=num_weeks
            )
            
        # Create decision variables for each class and time slot
        start = datetime.strptime(request.startDate, "%Y-%m-%d")
        end = datetime.strptime(request.endDate, "%Y-%m-%d")
        current = start
        
        self.variables = []
        
        while current <= end:
            if current.weekday() < 5:  # Weekdays only
                for period in range(1, 9):  # 8 periods per day
                    for class_obj in request.classes:
                        var = self.model.NewBoolVar(
                            f"{class_obj.name}_{current.date()}_{period}"
                        )
                        self.variables.append({
                            "variable": var,
                            "name": class_obj.name,
                            "date": current,
                            "period": period
                        })
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
    
    def apply_constraint(self, constraint: BaseConstraint, context: SchedulerContext) -> None:
        """
        Apply a constraint to the test context.
        
        Args:
            constraint: The constraint to test
            context: The scheduler context to apply it to
        """
        constraint.apply(context)
    
    def solve(self) -> bool:
        """
        Solve the model with applied constraints.
        Returns True if a solution was found.
        """
        status = self.solver.Solve(self.model)
        return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
    
    def get_solution_assignments(self, context: SchedulerContext) -> List[Dict[str, Any]]:
        """
        Get assignments from the solved model.
        
        Args:
            context: The scheduler context with solved model
            
        Returns:
            List of assignments with class name, date, and period
        """
        assignments = []
        
        for var_dict in self.variables:
            var = var_dict["variable"]
            if self.solver.Value(var) == 1:
                assignments.append({
                    "name": var_dict["name"],
                    "date": var_dict["date"],
                    "timeSlot": {"period": var_dict["period"]}
                })
                
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
        assignments = self.get_solution_assignments(context)
        return constraint.validate(assignments, context)

def create_test_harness() -> ConstraintTestHarness:
    """Factory function to create a fresh test harness"""
    return ConstraintTestHarness()
