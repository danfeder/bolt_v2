from typing import List, Dict, Any
import traceback
import time

from ..core import SchedulerContext
from ..constraints.assignment import SingleAssignmentConstraint, NoOverlapConstraint
from ..constraints.teacher import TeacherAvailabilityConstraint
from ..constraints.periods import RequiredPeriodsConstraint, ConflictPeriodsConstraint
from ..objectives.required import RequiredPeriodsObjective
from ..objectives.distribution import DistributionObjective, DistributionMetrics

from .base import BaseSolver
from ...models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleMetadata,
    ScheduleAssignment
)

class DevSolver(BaseSolver):
    """
    Development solver for testing new features and optimizations.
    Currently implementing:
    1. All stable solver features
    2. Enhanced distribution analysis
    3. Experimental scheduling patterns
    4. Detailed performance metrics
    """
    
    def __init__(self):
        super().__init__(name="cp-sat-dev")
        
        # Start with same configuration as stable solver
        self.add_constraint(SingleAssignmentConstraint())
        self.add_constraint(NoOverlapConstraint())
        self.add_constraint(TeacherAvailabilityConstraint())
        self.add_constraint(RequiredPeriodsConstraint())
        self.add_constraint(ConflictPeriodsConstraint())
        
        self.add_objective(RequiredPeriodsObjective())
        self.add_objective(DistributionObjective())
        
        # Track solver metrics
        self.last_run_metrics: Dict[str, Any] = {}
        
    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """
        Create a schedule using development configuration with enhanced metrics
        """
        start_time = time.time()
        print(f"\nStarting development solver for {len(request.classes)} classes...")
        
        try:
            # Create schedule using base solver
            response = super().create_schedule(request)
            
            # Calculate enhanced metrics
            distribution_objective = next(
                obj for obj in self.objectives 
                if isinstance(obj, DistributionObjective)
            )
            
            metrics = distribution_objective.calculate_metrics(
                response.assignments,
                SchedulerContext(
                    model=None,  # Not needed for metrics
                    solver=None,  # Not needed for metrics
                    request=request,
                    start_date=None,  # Not needed for metrics
                    end_date=None  # Not needed for metrics
                )
            )
            
            # Store metrics for analysis
            self.last_run_metrics = {
                "duration_ms": int((time.time() - start_time) * 1000),
                "distribution": {
                    "weekly": {
                        "classesPerWeek": metrics.classes_per_week,
                        "variance": metrics.week_variance
                    },
                    "daily": {
                        date: {
                            "periodSpread": metrics.period_spread[date],
                            "teacherLoadVariance": metrics.teacher_load_variance[date],
                            "classesByPeriod": periods
                        }
                        for date, periods in metrics.classes_per_period.items()
                    },
                    "score": metrics.distribution_score
                }
            }
            
            # Update response with enhanced metrics
            return ScheduleResponse(
                assignments=response.assignments,
                metadata=ScheduleMetadata(
                    solver=self.name,
                    duration=self.last_run_metrics["duration_ms"],
                    score=response.metadata.score,
                    distribution=self.last_run_metrics["distribution"]
                )
            )
            
        except Exception as e:
            print(f"Scheduling error in development solver: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            raise
    
    def get_last_run_metrics(self) -> Dict[str, Any]:
        """Get metrics from the last solver run"""
        return self.last_run_metrics.copy()  # Return copy to prevent modification
    
    def compare_with_stable(
        self,
        stable_response: ScheduleResponse,
        dev_response: ScheduleResponse
    ) -> Dict[str, Any]:
        """Compare development solver results with stable solver"""
        return {
            "assignment_differences": self._compare_assignments(
                stable_response.assignments,
                dev_response.assignments
            ),
            "metric_differences": {
                "score": dev_response.metadata.score - stable_response.metadata.score,
                "duration": (
                    dev_response.metadata.duration - 
                    stable_response.metadata.duration
                ),
                "distribution": self._compare_distribution(
                    stable_response.metadata.distribution,
                    dev_response.metadata.distribution
                )
            }
        }
    
    def _compare_assignments(
        self,
        stable_assignments: List[ScheduleAssignment],
        dev_assignments: List[ScheduleAssignment]
    ) -> Dict[str, Any]:
        """Compare assignment differences between solvers"""
        differences = []
        
        # Create lookup of stable assignments
        stable_map = {
            assignment.classId: assignment
            for assignment in stable_assignments
        }
        
        # Compare each development assignment
        for dev_assignment in dev_assignments:
            stable_assignment = stable_map.get(dev_assignment.classId)
            if not stable_assignment:
                differences.append({
                    "type": "missing_in_stable",
                    "classId": dev_assignment.classId,
                    "dev_assignment": dev_assignment
                })
                continue
                
            if (dev_assignment.date != stable_assignment.date or
                dev_assignment.timeSlot != stable_assignment.timeSlot):
                differences.append({
                    "type": "different_assignment",
                    "classId": dev_assignment.classId,
                    "stable": stable_assignment,
                    "dev": dev_assignment
                })
        
        # Check for assignments only in stable
        dev_map = {
            assignment.classId: assignment
            for assignment in dev_assignments
        }
        
        for stable_assignment in stable_assignments:
            if stable_assignment.classId not in dev_map:
                differences.append({
                    "type": "missing_in_dev",
                    "classId": stable_assignment.classId,
                    "stable_assignment": stable_assignment
                })
        
        return {
            "total_differences": len(differences),
            "differences": differences
        }
    
    def _compare_distribution(
        self,
        stable_dist: Dict[str, Any],
        dev_dist: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare distribution metrics between solvers"""
        return {
            "score_difference": (
                dev_dist.get("totalScore", 0) -
                stable_dist.get("totalScore", 0)
            ),
            "weekly_variance_difference": (
                dev_dist.get("weekly", {}).get("variance", 0) -
                stable_dist.get("weekly", {}).get("variance", 0)
            ),
            "average_period_spread_difference": (
                self._average_period_spread(dev_dist) -
                self._average_period_spread(stable_dist)
            )
        }
    
    def _average_period_spread(self, distribution: Dict[str, Any]) -> float:
        """Calculate average period spread across all days"""
        daily = distribution.get("daily", {})
        if not daily:
            return 0.0
            
        spreads = []
        for date_info in daily.values():
            if isinstance(date_info, dict):
                spread = date_info.get("periodSpread", 0)
                if spread is not None:
                    spreads.append(spread)
        
        return (
            sum(spreads) / len(spreads)
            if spreads
            else 0.0
        )
