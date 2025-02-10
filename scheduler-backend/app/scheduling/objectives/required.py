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
    2. Preferred period assignments (weighted by class preference)
    3. Avoiding certain periods (weighted by class avoidance)
    4. Earlier dates (lowest priority)
    """
    
    def __init__(self):
        super().__init__(
            name="required_periods",
            weight=1000  # High weight since this is primary objective
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        terms = []
        start_date = context.start_date
        
        for var in context.variables:
            # Get class object for this variable
            class_obj = next(
                c for c in context.request.classes 
                if c.id == var["classId"]
            )
            weekday = var["date"].weekday() + 1
            period = var["period"]
            
            # Check if this is a required period
            is_required = any(
                rp.dayOfWeek == weekday and rp.period == period
                for rp in class_obj.weeklySchedule.requiredPeriods
            )
            
            if is_required:
                # Large reward for required periods (highest priority)
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
            terms.append(int(date_weight) * var["variable"])
        
        return terms
