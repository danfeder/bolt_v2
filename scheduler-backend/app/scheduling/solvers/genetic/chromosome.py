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
    
    def crossover(self, other: 'ScheduleChromosome', method: str = "auto") -> tuple['ScheduleChromosome', 'ScheduleChromosome']:
        """
        Perform crossover with another chromosome.
        
        Args:
            other: The other parent chromosome
            method: Crossover method to use:
                - "single_point": Classic single-point crossover
                - "two_point": Two-point crossover
                - "uniform": Uniform crossover with 0.5 probability for each gene
                - "order": Order-based crossover that preserves relative ordering
                - "auto": Automatically select the best method based on chromosome
                
        Returns:
            A tuple of two child chromosomes
        """
        if len(self.genes) != len(other.genes):
            raise ValueError("Chromosomes must have same number of genes for crossover")
            
        # Choose method if auto
        if method == "auto":
            # Use different methods based on problem characteristics
            if len(self.genes) <= 10:
                method = "uniform"  # Good for small chromosomes
            elif self.request and self.request.constraints.maxClassesPerDay > 0:
                method = "order"    # Good for preserving scheduling patterns
            else:
                method = random.choice(["single_point", "two_point", "uniform"])
                
        # Execute the selected crossover method
        if method == "single_point":
            return self._single_point_crossover(other)
        elif method == "two_point":
            return self._two_point_crossover(other)
        elif method == "uniform":
            return self._uniform_crossover(other)
        elif method == "order":
            return self._order_crossover(other)
        else:
            raise ValueError(f"Unknown crossover method: {method}")
    
    def _single_point_crossover(self, other: 'ScheduleChromosome') -> tuple['ScheduleChromosome', 'ScheduleChromosome']:
        """
        Perform single-point crossover with another chromosome.
        
        This is the classic crossover that splits the chromosome at a random point.
        """
        # Create new chromosomes
        child1 = ScheduleChromosome(self.request)
        child2 = ScheduleChromosome(self.request)
        
        # Select crossover point
        crossover_point = random.randint(0, len(self.genes))
        
        # Create children by combining genes from parents
        child1.genes = self.genes[:crossover_point] + other.genes[crossover_point:]
        child2.genes = other.genes[:crossover_point] + self.genes[crossover_point:]
        
        return child1, child2
    
    def _two_point_crossover(self, other: 'ScheduleChromosome') -> tuple['ScheduleChromosome', 'ScheduleChromosome']:
        """
        Perform two-point crossover with another chromosome.
        
        Takes a section from the middle of one parent and combines with
        the beginning and end of the other parent.
        """
        # Create new chromosomes
        child1 = ScheduleChromosome(self.request)
        child2 = ScheduleChromosome(self.request)
        
        # Select two crossover points
        length = len(self.genes)
        point1 = random.randint(0, length - 1)
        point2 = random.randint(point1 + 1, length)
        
        # Create children by combining genes from parents
        child1.genes = (
            self.genes[:point1] +
            other.genes[point1:point2] + 
            self.genes[point2:]
        )
        
        child2.genes = (
            other.genes[:point1] +
            self.genes[point1:point2] + 
            other.genes[point2:]
        )
        
        return child1, child2
    
    def _uniform_crossover(self, other: 'ScheduleChromosome') -> tuple['ScheduleChromosome', 'ScheduleChromosome']:
        """
        Perform uniform crossover with another chromosome.
        
        Each gene has a 50% chance of coming from either parent.
        This provides more mixing and is better for some problems.
        """
        # Create new chromosomes
        child1 = ScheduleChromosome(self.request)
        child2 = ScheduleChromosome(self.request)
        
        child1.genes = []
        child2.genes = []
        
        # For each gene position, randomly select from either parent
        for i in range(len(self.genes)):
            # Flip a coin for each gene
            if random.random() < 0.5:
                child1.genes.append(self.genes[i])
                child2.genes.append(other.genes[i])
            else:
                child1.genes.append(other.genes[i])
                child2.genes.append(self.genes[i])
        
        return child1, child2
    
    def _order_crossover(self, other: 'ScheduleChromosome') -> tuple['ScheduleChromosome', 'ScheduleChromosome']:
        """
        Perform order-based crossover with another chromosome.
        
        This preserves the relative ordering of genes, which is important
        for scheduling problems where the order of classes matters.
        """
        # Create new chromosomes
        child1 = ScheduleChromosome(self.request)
        child2 = ScheduleChromosome(self.request)
        
        length = len(self.genes)
        
        # Select a random segment
        start = random.randint(0, length - 2)
        end = random.randint(start + 1, length - 1)
        
        # Create a map of class IDs to genes for quick lookup
        self_class_map = {gene.class_id: gene for gene in self.genes}
        other_class_map = {gene.class_id: gene for gene in other.genes}
        
        # Get class IDs from the segments we'll preserve
        segment1 = [gene.class_id for gene in self.genes[start:end]]
        segment2 = [gene.class_id for gene in other.genes[start:end]]
        
        # Initialize child genes
        child1.genes = [None] * length
        child2.genes = [None] * length
        
        # Copy the selected segments
        for i in range(start, end):
            child1.genes[i] = self.genes[i]
            child2.genes[i] = other.genes[i]
        
        # Fill remaining positions while preserving order
        self._fill_remaining_order_based(child1, other, segment1, start, end)
        self._fill_remaining_order_based(child2, self, segment2, start, end)
        
        return child1, child2
    
    def _fill_remaining_order_based(
        self, 
        child: 'ScheduleChromosome', 
        donor: 'ScheduleChromosome',
        used_classes: List[str],
        start: int,
        end: int
    ) -> None:
        """
        Helper method for order crossover to fill remaining positions.
        
        Args:
            child: The child chromosome to fill
            donor: The chromosome providing the genes for remaining positions
            used_classes: List of class IDs already used in the fixed segment
            start: Start index of the fixed segment
            end: End index of the fixed segment
        """
        length = len(child.genes)
        donor_classes = [gene.class_id for gene in donor.genes]
        
        # Rearrange the donor classes to put the used ones at the end
        donor_order = []
        for class_id in donor_classes:
            if class_id not in used_classes:
                donor_order.append(class_id)
        
        # Fill positions before the fixed segment
        idx = 0
        for i in range(0, start):
            child.genes[i] = next(
                gene for gene in donor.genes 
                if gene.class_id == donor_order[idx]
            )
            idx += 1
            
        # Fill positions after the fixed segment
        for i in range(end, length):
            child.genes[i] = next(
                gene for gene in donor.genes 
                if gene.class_id == donor_order[idx]
            )
            idx += 1
    
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
        
        # 3. Check consecutive classes constraint
        # Group by week and day
        daily_schedule: Dict[tuple[int, int], List[int]] = {}
        for gene in self.genes:
            key = (gene.week, gene.day_of_week)
            if key not in daily_schedule:
                daily_schedule[key] = []
            daily_schedule[key].append(gene.period)
        
        # Check for three consecutive classes (always disallowed)
        for periods in daily_schedule.values():
            periods.sort()
            
            # Check sequences of three consecutive periods
            for i in range(len(periods) - 2):
                if (periods[i+1] == periods[i] + 1 and 
                    periods[i+2] == periods[i+1] + 1):
                    # Three consecutive periods found - not allowed
                    return False
            
            # Check if pairs are allowed
            allow_consecutive_pairs = True
            if hasattr(constraints, 'allowConsecutiveClasses'):
                allow_consecutive_pairs = constraints.allowConsecutiveClasses
            
            # If we don't allow consecutive pairs, check for them
            if not allow_consecutive_pairs:
                for i in range(len(periods) - 1):
                    if periods[i+1] == periods[i] + 1:
                        # Consecutive pair found when not allowed
                        return False
        
        return True
