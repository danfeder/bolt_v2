from typing import List
from dateutil import parser
from dateutil.tz import UTC

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext

class RequiredPeriodsObjective(BaseObjective):
    """
    Objective function prioritizing:
    1. Required period assignments (highest priority)
    2. Early scheduling in last week (medium priority)
    3. Earlier dates (lowest priority)
    """
    
    def __init__(self):
        super().__init__(
            name="required_periods",
            weight=1000  # High weight since this is primary objective
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        start_date = context.start_date
        
        # Add early scheduling variables from context
        early_vars = context.debug_info.get("early_scheduling_vars", [])
        for var in early_vars:
            # Weight of 5000 puts this between required periods (10000) and other objectives
            terms.append(5000 * var)
        
        for var in context.variables:
            # Get class object for this variable
            class_obj = next(
                c for c in context.request.classes 
                if c.name == var["name"]
            )
            
            # Convert variable's date to date string
            date_str = var["date"].date().isoformat()
            period = var["period"]
            
            # Check if this is a required period
            # Handle different class models (direct required_periods or nested in weeklySchedule)
            is_required = False
            if hasattr(class_obj, "required_periods") and class_obj.required_periods:
                is_required = any(
                    rp.date == date_str and rp.period == period
                    for rp in class_obj.required_periods
                )
            elif hasattr(class_obj, "weeklySchedule") and hasattr(class_obj.weeklySchedule, "requiredPeriods"):
                # Get weekday from date (1-7 for Monday-Sunday)
                weekday = var["date"].weekday() + 1
                is_required = any(
                    rp.dayOfWeek == weekday and rp.period == period
                    for rp in class_obj.weeklySchedule.requiredPeriods
                )
            
            if is_required:
                # Large reward for required periods (highest priority)
                terms.append(10000 * var["variable"])
                
            # Small reward for earlier dates (lowest priority)
            days_from_start = (var["date"] - start_date).days
            date_weight = 10 - days_from_start * 0.1
            terms.append(int(date_weight) * var["variable"])
        
        return terms
