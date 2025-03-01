"""Grade-level grouping objective for optimizing similar grade placement."""
from collections import defaultdict
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

from ortools.sat.python import cp_model

from .base import BaseObjective
from ..core import SchedulerContext
from ...models import ScheduleAssignment, Class

# Define similarity scores (higher means more similar)
def grade_similarity(grade1_val: int, grade2_val: int) -> float:
    """
    Calculate similarity score between two grade groups (higher is more similar).
    
    Args:
        grade1_val: Numeric grade group for first class
        grade2_val: Numeric grade group for second class
        
    Returns:
        Similarity score from 0.0 (not similar) to 1.0 (identical)
    """
    # Calculate similarity based on how close grades are to each other
    diff = abs(grade1_val - grade2_val)
    
    # Similarity score decreases with grade difference
    if diff == 0:  # Same grade
        return 1.0
    elif diff == 1:  # Adjacent grades (e.g., K and 1st)
        return 0.8
    elif diff == 2:  # Two grades apart (e.g., 1st and 3rd)
        return 0.4
    else:  # Grades far apart
        return 0.0

@dataclass
class GradeGroupingMetrics:
    """Metrics for grade level grouping evaluation."""
    transitions: int  # Total number of grade level transitions
    similar_pairs: int  # Number of consecutive similar-grade pairs
    dissimilar_pairs: int  # Number of consecutive dissimilar-grade pairs
    daily_grouping_scores: Dict[str, float]  # Grouping score by day
    grouping_score: float  # Overall grouping score

class GradeGroupingObjective(BaseObjective):
    """
    Objective that rewards scheduling similar grade levels in consecutive periods.
    This reduces equipment changes and activity transitions.
    """
    
    def __init__(self):
        from ..solvers.config import WEIGHTS
        super().__init__(
            name="grade_grouping",
            weight=WEIGHTS.get('grade_grouping', 1000)  # Default weight if not in config
        )
    
    def create_terms(self, context: SchedulerContext) -> List[cp_model.LinearExpr]:
        """
        Create objective terms that reward consecutive similar grade scheduling.
        """
        terms = []
        
        # Group variables by date and period to find consecutive assignments
        by_date_period = defaultdict(dict)
        for var in context.variables:
            date = var["date"].date()
            period = var["period"]
            by_date_period[date][period] = var
        
        # Create reward terms for consecutive periods with similar grades
        for date, periods in by_date_period.items():
            period_nums = sorted(periods.keys())
            for i in range(len(period_nums) - 1):
                # Get current and next period
                cur_period = period_nums[i]
                next_period = period_nums[i + 1]
                
                # Skip if periods are not consecutive
                if next_period != cur_period + 1:
                    continue
                
                cur_var = periods[cur_period]
                next_var = periods[next_period]
                
                # Create variables to track if both periods are scheduled
                cur_active = cur_var["variable"]
                next_active = next_var["variable"]
                
                # Create variable for when both periods are active
                both_active = context.model.NewBoolVar(
                    f"both_active_{date}_{cur_period}_{next_period}"
                )
                context.model.AddBoolAnd([cur_active, next_active]).OnlyEnforceIf(both_active)
                context.model.AddBoolOr([cur_active.Not(), next_active.Not()]).OnlyEnforceIf(both_active.Not())
                
                # Get class objects for both variables
                # Handle different field names (id vs name vs classId)
                cur_class = next((c for c in context.request.classes if 
                                  (hasattr(c, "id") and c.id == cur_var["name"]) or 
                                  (hasattr(c, "name") and c.name == cur_var["name"])), None)
                next_class = next((c for c in context.request.classes if 
                                  (hasattr(c, "id") and c.id == next_var["name"]) or 
                                  (hasattr(c, "name") and c.name == next_var["name"])), None)
                
                if cur_class and next_class:
                    # Calculate similarity score between the grades using gradeGroup
                    cur_grade_group = getattr(cur_class, 'gradeGroup', None)
                    next_grade_group = getattr(next_class, 'gradeGroup', None)
                    
                    # If gradeGroup is not available, use the mapping from the model
                    if cur_grade_group is None or next_grade_group is None:
                        # Default grade mapping
                        grade_map = {
                            "Pre-K": 0,
                            "K": 1,
                            "1": 2,
                            "2": 3,
                            "3": 4,
                            "4": 5,
                            "5": 6
                        }
                        cur_grade_group = grade_map.get(cur_class.grade, 0)
                        next_grade_group = grade_map.get(next_class.grade, 0)
                    
                    # Calculate similarity
                    similarity = grade_similarity(cur_grade_group, next_grade_group)
                    
                    # Convert to integer score (multiply by 100 for CP-SAT)
                    int_score = int(similarity * 100)
                    
                    # Only add bonus if similarity is meaningful
                    if int_score > 0:
                        # Create reward term when both are active
                        reward = context.model.NewIntVar(
                            0, int_score, 
                            f"grade_grouping_reward_{date}_{cur_period}_{next_period}"
                        )
                        
                        # Set reward to similarity score if both active, otherwise 0
                        context.model.Add(reward == int_score).OnlyEnforceIf(both_active)
                        context.model.Add(reward == 0).OnlyEnforceIf(both_active.Not())
                        
                        terms.append(reward)
        
        return terms
    
    def calculate_metrics(
        self,
        assignments: List[ScheduleAssignment],
        context: SchedulerContext
    ) -> GradeGroupingMetrics:
        """
        Calculate grade grouping metrics for the schedule.
        
        Args:
            assignments: Schedule assignments
            context: Scheduler context
            
        Returns:
            Grade grouping metrics
        """
        # Group assignments by date and period
        by_date_period = defaultdict(dict)
        
        # Get class objects for lookups
        class_map = {c.id: c for c in context.request.classes}
        
        # Process assignments
        for assignment in assignments:
            date = assignment.date
            period = assignment.timeSlot.period
            class_id = assignment.name  # Using name as class ID
            by_date_period[date][period] = class_id
        
        # Calculate metrics
        total_transitions = 0
        similar_pairs = 0
        dissimilar_pairs = 0
        daily_scores = {}
        
        for date, periods in by_date_period.items():
            period_nums = sorted(periods.keys())
            day_transitions = 0
            day_similar = 0
            day_dissimilar = 0
            
            for i in range(len(period_nums) - 1):
                cur_period = period_nums[i]
                next_period = period_nums[i + 1]
                
                # Skip if periods are not consecutive
                if next_period != cur_period + 1:
                    continue
                
                cur_class_id = periods[cur_period]
                next_class_id = periods[next_period]
                
                # Get grade levels
                cur_class = class_map.get(cur_class_id, None)
                next_class = class_map.get(next_class_id, None)
                
                if cur_class and next_class:
                    # Get grade groups
                    cur_grade_group = getattr(cur_class, 'gradeGroup', None)
                    next_grade_group = getattr(next_class, 'gradeGroup', None)
                    
                    # If gradeGroup is not available, use the mapping from the model
                    if cur_grade_group is None or next_grade_group is None:
                        # Default grade mapping
                        grade_map = {
                            "Pre-K": 0,
                            "K": 1,
                            "1": 2,
                            "2": 3,
                            "3": 4,
                            "4": 5,
                            "5": 6
                        }
                        cur_grade_group = grade_map.get(cur_class.grade, 0)
                        next_grade_group = grade_map.get(next_class.grade, 0)
                    
                    # Calculate similarity
                    similarity = grade_similarity(cur_grade_group, next_grade_group)
                    
                    day_transitions += 1
                    if similarity >= 0.4:  # Threshold for similar
                        day_similar += 1
                    else:
                        day_dissimilar += 1
            
            # Calculate day score
            total_transitions += day_transitions
            similar_pairs += day_similar
            dissimilar_pairs += day_dissimilar
            
            # Calculate day score (percentage of transitions that are good)
            day_score = day_similar / day_transitions if day_transitions > 0 else 1.0
            daily_scores[date] = day_score
        
        # Calculate overall score
        total_score = 0
        if total_transitions > 0:
            # Score based on percentage of similar transitions
            similarity_ratio = similar_pairs / total_transitions
            total_score = similarity_ratio * 1000
        
        return GradeGroupingMetrics(
            transitions=total_transitions,
            similar_pairs=similar_pairs,
            dissimilar_pairs=dissimilar_pairs,
            daily_grouping_scores=daily_scores,
            grouping_score=total_score
        )