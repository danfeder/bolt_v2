"""Fitness calculation for genetic algorithm scheduling."""
from datetime import datetime
from typing import Dict, List

from ....models import (
    ScheduleRequest,
    Class,
    TimeSlot,
    WeightConfig
)
from .chromosome import ScheduleChromosome, Gene

class FitnessCalculator:
    """Calculates fitness scores for schedule chromosomes."""
    
    def __init__(self, request: ScheduleRequest, weights: WeightConfig):
        """
        Initialize fitness calculator.
        
        Args:
            request: Schedule request containing classes and constraints
            weights: Configuration of weights for different objectives
        """
        self.request = request
        self.weights = weights
        
    def calculate_fitness(self, chromosome: ScheduleChromosome) -> float:
        """
        Calculate fitness score for a chromosome.
        
        Higher scores indicate better solutions. Negative values
        indicate constraint violations.
        """
        if not chromosome.validate():
            return float('-inf')  # Invalid solutions get worst possible score
            
        score = 0.0
        
        # Calculate different components of the fitness
        score += self._evaluate_conflicts(chromosome) 
        score += self._evaluate_preferred_periods(chromosome)
        score += self._evaluate_distribution(chromosome)
        score += self._evaluate_consecutive_classes(chromosome)
        score += self._evaluate_early_scheduling(chromosome)
        
        return score
        
    def _evaluate_conflicts(self, chromosome: ScheduleChromosome) -> float:
        """Evaluate conflict-related constraints."""
        score = 0.0
        
        # Group assignments by time slot
        time_slots: Dict[tuple[int, int, int], List[str]] = {}  # (week, day, period) -> [class_ids]
        for gene in chromosome.genes:
            key = (gene.week, gene.day_of_week, gene.period)
            if key not in time_slots:
                time_slots[key] = []
            time_slots[key].append(gene.class_id)
            
        # Check each class's conflicts
        for class_obj in self.request.classes:
            class_genes = [g for g in chromosome.genes if g.class_id == class_obj.id]
            
            # Check weekly schedule conflicts
            for gene in class_genes:
                time_slot = TimeSlot(dayOfWeek=gene.day_of_week, period=gene.period)
                
                # Heavy penalty for scheduling during conflicts
                if any(
                    conflict.dayOfWeek == time_slot.dayOfWeek and
                    conflict.period == time_slot.period
                    for conflict in class_obj.weeklySchedule.conflicts
                ):
                    score -= 10000  # Large penalty for conflict violations
                    
        return score
        
    def _evaluate_preferred_periods(self, chromosome: ScheduleChromosome) -> float:
        """Evaluate preference satisfaction."""
        score = 0.0
        
        for class_obj in self.request.classes:
            class_genes = [g for g in chromosome.genes if g.class_id == class_obj.id]
            
            for gene in class_genes:
                time_slot = TimeSlot(dayOfWeek=gene.day_of_week, period=gene.period)
                
                # Reward for preferred periods
                if any(
                    pref.dayOfWeek == time_slot.dayOfWeek and
                    pref.period == time_slot.period
                    for pref in class_obj.weeklySchedule.preferredPeriods
                ):
                    score += self.weights.preferred_periods
                    
                # Penalty for avoided periods
                if any(
                    avoid.dayOfWeek == time_slot.dayOfWeek and
                    avoid.period == time_slot.period
                    for avoid in class_obj.weeklySchedule.avoidPeriods
                ):
                    score += self.weights.avoid_periods
                    
        return score
        
    def _evaluate_distribution(self, chromosome: ScheduleChromosome) -> float:
        """Evaluate class distribution across schedule."""
        score = 0.0
        
        # Count classes per week
        classes_per_week: Dict[int, int] = {}
        for gene in chromosome.genes:
            classes_per_week[gene.week] = classes_per_week.get(gene.week, 0) + 1
            
        # Penalize uneven distribution
        if classes_per_week:
            avg_classes = sum(classes_per_week.values()) / len(classes_per_week)
            variance = sum(
                (count - avg_classes) ** 2 
                for count in classes_per_week.values()
            ) / len(classes_per_week)
            
            # Lower variance is better
            score -= variance * self.weights.distribution
            
        return score
        
    def _evaluate_consecutive_classes(self, chromosome: ScheduleChromosome) -> float:
        """Evaluate consecutive classes penalties."""
        score = 0.0
        constraints = self.request.constraints
        
        # Group by day
        daily_schedule: Dict[tuple[int, int], List[int]] = {}
        for gene in chromosome.genes:
            key = (gene.week, gene.day_of_week)
            if key not in daily_schedule:
                daily_schedule[key] = []
            daily_schedule[key].append(gene.period)
            
        # Check consecutive periods
        for periods in daily_schedule.values():
            periods.sort()
            consecutive_count = 1
            for i in range(1, len(periods)):
                if periods[i] == periods[i-1] + 1:
                    consecutive_count += 1
                    if consecutive_count > constraints.maxConsecutiveClasses:
                        # Soft penalty for consecutive classes beyond limit
                        score -= 500 * (consecutive_count - constraints.maxConsecutiveClasses)
                else:
                    consecutive_count = 1
                    
        return score
        
    def _evaluate_early_scheduling(self, chromosome: ScheduleChromosome) -> float:
        """Evaluate preference for earlier scheduling."""
        score = 0.0
        
        # Small bonus for scheduling in earlier weeks
        total_weeks = (chromosome.end_date - chromosome.start_date).days // 7 + 1
        for gene in chromosome.genes:
            # Higher bonus for earlier weeks
            score += self.weights.earlier_dates * (total_weeks - gene.week) / total_weeks
            
        return score
