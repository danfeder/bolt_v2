"""Chromosome representation for genetic algorithm scheduling."""
from typing import List, Dict, Optional
from dataclasses import dataclass
import random
from datetime import datetime, timedelta

from ....models import (
    ScheduleRequest,
    ScheduleResponse,
    ScheduleAssignment,
    ScheduleMetadata,
    TimeSlot,
    Class
)

@dataclass
class Gene:
    """Represents a single class assignment within the chromosome."""
    class_id: str
    day_of_week: int  # 1-5 (Monday-Friday)
    period: int       # 1-8
    week: int        # Week number relative to start date
    
    def to_time_slot(self) -> TimeSlot:
        """Convert gene to TimeSlot model."""
        return TimeSlot(dayOfWeek=self.day_of_week, period=self.period)

class ScheduleChromosome:
    """
    Genetic representation of a complete schedule.
    
    Each chromosome contains a list of genes, where each gene represents
    a class assignment (what class is scheduled for what time slot).
    """
    
    def __init__(self, request: Optional[ScheduleRequest] = None):
        self.genes: List[Gene] = []
        self.fitness: float = 0.0
        self.request = request
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        
        if request:
            self.start_date = datetime.strptime(request.startDate, "%Y-%m-%d")
            self.end_date = datetime.strptime(request.endDate, "%Y-%m-%d")
    
    def initialize_random(self) -> None:
        """Create a random initial schedule."""
        if not self.request:
            raise ValueError("Cannot initialize without a ScheduleRequest")
            
        self.genes = []
        total_weeks = (self.end_date - self.start_date).days // 7 + 1
        
        for class_obj in self.request.classes:
            # Calculate how many sessions this class needs based on constraints
            sessions_needed = self.request.constraints.minPeriodsPerWeek * total_weeks
            
            for _ in range(sessions_needed):
                gene = self._create_random_gene(class_obj.id)
                self.genes.append(gene)
    
    def _create_random_gene(self, class_id: str) -> Gene:
        """Create a random gene (class assignment) respecting basic time constraints."""
        if not self.request:
            raise ValueError("Cannot create genes without a ScheduleRequest")
            
        # Random day (1-5, Monday-Friday)
        day = random.randint(1, 5)
        
        # Random period (1-8)
        period = random.randint(1, 8)
        
        # Random week within the schedule range
        total_weeks = (self.end_date - self.start_date).days // 7 + 1
        week = random.randint(0, total_weeks - 1)
        
        return Gene(
            class_id=class_id,
            day_of_week=day,
            period=period,
            week=week
        )
    
    def mutate(self, mutation_rate: float = 0.1) -> None:
        """
        Apply random mutations to genes.
        
        Args:
            mutation_rate: Probability (0-1) of each gene being mutated
        """
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                # Replace with a new random gene for the same class
                self.genes[i] = self._create_random_gene(self.genes[i].class_id)
    
    def crossover(self, other: 'ScheduleChromosome') -> tuple['ScheduleChromosome', 'ScheduleChromosome']:
        """
        Perform crossover with another chromosome.
        
        Uses single-point crossover to create two offspring.
        """
        if len(self.genes) != len(other.genes):
            raise ValueError("Chromosomes must have same number of genes for crossover")
            
        # Create new chromosomes
        child1 = ScheduleChromosome(self.request)
        child2 = ScheduleChromosome(self.request)
        
        # Select crossover point
        crossover_point = random.randint(0, len(self.genes))
        
        # Create children by combining genes from parents
        child1.genes = self.genes[:crossover_point] + other.genes[crossover_point:]
        child2.genes = other.genes[:crossover_point] + self.genes[crossover_point:]
        
        return child1, child2
    
    def encode(self, schedule: ScheduleResponse) -> None:
        """Convert a ScheduleResponse into chromosome representation."""
        self.genes = []
        current_date = self.start_date
        
        for assignment in schedule.assignments:
            # Calculate week number
            assignment_date = datetime.strptime(assignment.date, "%Y-%m-%d")
            week = (assignment_date - self.start_date).days // 7
            
            # Create gene from assignment
            gene = Gene(
                class_id=assignment.name,
                day_of_week=assignment.timeSlot.dayOfWeek,
                period=assignment.timeSlot.period,
                week=week
            )
            self.genes.append(gene)
    
    def decode(self) -> ScheduleResponse:
        """Convert chromosome representation into a ScheduleResponse."""
        assignments: List[ScheduleAssignment] = []
        
        for gene in self.genes:
            # Calculate actual date from week and day
            days_to_add = gene.week * 7 + (gene.day_of_week - 1)
            assignment_date = self.start_date + timedelta(days=days_to_add)
            
            assignment = ScheduleAssignment(
                name=gene.class_id,
                date=assignment_date.strftime("%Y-%m-%d"),
                timeSlot=gene.to_time_slot()
            )
            assignments.append(assignment)
        
        # Create basic metadata (will be updated with actual values later)
        metadata = ScheduleMetadata(
            duration_ms=0,
            solutions_found=1,
            score=self.fitness,
            gap=0.0
        )
        
        return ScheduleResponse(assignments=assignments, metadata=metadata)
    
    def validate(self) -> bool:
        """
        Check if the chromosome represents a valid schedule.
        
        Returns:
            bool: True if schedule is valid, False otherwise
        """
        if not self.request:
            raise ValueError("Cannot validate without a ScheduleRequest")
            
        # Check basic constraints
        constraints = self.request.constraints
        
        # 1. Check classes per day constraint
        classes_per_day: Dict[tuple[int, int], int] = {}  # (week, day) -> count
        for gene in self.genes:
            key = (gene.week, gene.day_of_week)
            classes_per_day[key] = classes_per_day.get(key, 0) + 1
            if classes_per_day[key] > constraints.maxClassesPerDay:
                return False
        
        # 2. Check classes per week constraint
        classes_per_week: Dict[int, int] = {}
        for gene in self.genes:
            classes_per_week[gene.week] = classes_per_week.get(gene.week, 0) + 1
            if classes_per_week[gene.week] > constraints.maxClassesPerWeek:
                return False
        
        # 3. Check consecutive classes if it's a hard constraint
        if constraints.consecutiveClassesRule == "hard":
            # Group by week and day
            daily_schedule: Dict[tuple[int, int], List[int]] = {}
            for gene in self.genes:
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
                            return False
                    else:
                        consecutive_count = 1
        
        return True
