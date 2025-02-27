"""Adaptive parameter controller for genetic algorithm."""
from typing import Dict, List, Optional, Tuple
import numpy as np


class AdaptiveController:
    """
    Controls adaptive parameter adjustments for genetic algorithm.
    
    This controller adjusts mutation and crossover rates based on
    population diversity and convergence metrics to maintain a
    balance between exploration and exploitation.
    """
    
    def __init__(
        self,
        base_mutation_rate: float = 0.1,
        base_crossover_rate: float = 0.8,
        min_mutation_rate: float = 0.05,
        max_mutation_rate: float = 0.3,
        min_crossover_rate: float = 0.6,
        max_crossover_rate: float = 0.95,
        diversity_threshold: float = 0.15,
        adaptation_strength: float = 0.5,
        history_window: int = 5,
        adaptation_interval: int = 5
    ):
        """
        Initialize adaptive controller.
        
        Args:
            base_mutation_rate: Default mutation rate
            base_crossover_rate: Default crossover rate
            min_mutation_rate: Minimum allowed mutation rate
            max_mutation_rate: Maximum allowed mutation rate
            min_crossover_rate: Minimum allowed crossover rate
            max_crossover_rate: Maximum allowed crossover rate
            diversity_threshold: Threshold below which to increase mutation
            adaptation_strength: How strongly to adapt parameters (0.0-1.0)
            history_window: Number of generations to track for trends
            adaptation_interval: Generations between parameter adjustments
        """
        # Base parameters
        self.base_mutation_rate = base_mutation_rate
        self.base_crossover_rate = base_crossover_rate
        
        # Current parameters
        self.current_mutation_rate = base_mutation_rate
        self.current_crossover_rate = base_crossover_rate
        
        # Parameter limits
        self.min_mutation_rate = min_mutation_rate
        self.max_mutation_rate = max_mutation_rate
        self.min_crossover_rate = min_crossover_rate
        self.max_crossover_rate = max_crossover_rate
        
        # Adaptation settings
        self.diversity_threshold = diversity_threshold
        self.adaptation_strength = adaptation_strength
        self.history_window = history_window
        self.adaptation_interval = adaptation_interval
        
        # History tracking
        self.diversity_history: List[float] = []
        self.fitness_history: List[float] = []
        self.last_adaptation_generation = 0
        
    def should_adapt(self, generation: int) -> bool:
        """
        Determine if parameters should be adapted on this generation.
        
        Args:
            generation: Current generation number
            
        Returns:
            True if parameters should be adapted, False otherwise
        """
        return (generation - self.last_adaptation_generation) >= self.adaptation_interval

    def update_history(
        self,
        best_fitness: float,
        diversity: float
    ) -> None:
        """
        Update history with current generation metrics.
        
        Args:
            best_fitness: Best fitness in current population
            diversity: Current population diversity
        """
        self.diversity_history.append(diversity)
        self.fitness_history.append(best_fitness)
        
        # Keep history limited to window size
        if len(self.diversity_history) > self.history_window:
            self.diversity_history.pop(0)
        if len(self.fitness_history) > self.history_window:
            self.fitness_history.pop(0)
    
    def get_diversity_trend(self) -> float:
        """
        Calculate the trend in diversity over recent generations.
        
        Returns:
            A value between -1.0 and 1.0, where:
            - Negative values indicate decreasing diversity
            - Positive values indicate increasing diversity
            - Zero indicates stable diversity
        """
        if len(self.diversity_history) < 2:
            return 0.0
            
        # Use linear regression slope to determine trend
        x = np.arange(len(self.diversity_history))
        y = np.array(self.diversity_history)
        slope, _ = np.polyfit(x, y, 1)
        
        # Normalize slope to -1.0 to 1.0 range
        max_slope = 0.05  # This value may need tuning
        normalized_slope = max(-1.0, min(1.0, slope / max_slope))
        
        return normalized_slope
    
    def get_convergence_rate(self) -> float:
        """
        Calculate the convergence rate based on fitness improvement.
        
        Returns:
            A value between 0.0 and 1.0, where:
            - 0.0 indicates no improvement (stagnation)
            - 1.0 indicates rapid improvement
        """
        if len(self.fitness_history) < 2:
            return 0.5  # Default to middle value
            
        improvements = []
        for i in range(1, len(self.fitness_history)):
            rel_improvement = (self.fitness_history[i] - self.fitness_history[i-1])
            # Normalize by max fitness to get proportional improvement
            max_fitness = max(abs(f) for f in self.fitness_history)
            if max_fitness > 0:
                rel_improvement /= max_fitness
            improvements.append(rel_improvement)
            
        # Use average of recent improvements
        avg_improvement = sum(improvements) / len(improvements)
        
        # Convert to 0-1 range
        max_expected_improvement = 0.05  # This value may need tuning
        convergence_rate = max(0.0, min(1.0, avg_improvement / max_expected_improvement))
        
        return convergence_rate
        
    def adjust_mutation_rate(
        self,
        diversity: float,
        diversity_trend: float
    ) -> float:
        """
        Adjust mutation rate based on population diversity.
        
        Args:
            diversity: Current population diversity
            diversity_trend: Trend in diversity over time
            
        Returns:
            Adjusted mutation rate
        """
        # Base adjustment on current diversity
        if diversity < self.diversity_threshold:
            # Low diversity - increase mutation to explore more
            adjustment = self.adaptation_strength * (
                (self.diversity_threshold - diversity) / self.diversity_threshold
            )
            new_rate = self.base_mutation_rate + adjustment * (
                self.max_mutation_rate - self.base_mutation_rate
            )
        else:
            # Good diversity - reduce toward base rate
            adjustment = self.adaptation_strength * 0.5  # Gentler adjustment downward
            new_rate = self.base_mutation_rate + (
                self.current_mutation_rate - self.base_mutation_rate
            ) * (1 - adjustment)
        
        # Further adjust based on diversity trend
        if diversity_trend < -0.2:  # Significant downward trend
            # Increase mutation more aggressively when diversity is dropping rapidly
            trend_adjustment = -diversity_trend * self.adaptation_strength * 0.3
            new_rate += trend_adjustment * (self.max_mutation_rate - self.base_mutation_rate)
            
        # Clamp to allowed range
        return max(self.min_mutation_rate, min(self.max_mutation_rate, new_rate))
        
    def adjust_crossover_rate(
        self,
        convergence_rate: float,
        diversity: float
    ) -> float:
        """
        Adjust crossover rate based on convergence rate and diversity.
        
        Args:
            convergence_rate: Rate of fitness improvement
            diversity: Current population diversity
            
        Returns:
            Adjusted crossover rate
        """
        # In early convergence with good diversity, increase crossover
        # to combine good solutions
        if convergence_rate > 0.5 and diversity > self.diversity_threshold:
            adjustment = self.adaptation_strength * convergence_rate * 0.5
            new_rate = self.base_crossover_rate + adjustment * (
                self.max_crossover_rate - self.base_crossover_rate
            )
        # In stagnation with low diversity, decrease crossover
        # to allow more mutation to explore
        elif convergence_rate < 0.2 and diversity < self.diversity_threshold:
            adjustment = self.adaptation_strength * (1 - convergence_rate) * 0.5
            new_rate = self.base_crossover_rate - adjustment * (
                self.base_crossover_rate - self.min_crossover_rate
            )
        # Otherwise, gradual return to base rate
        else:
            adjustment = self.adaptation_strength * 0.3
            new_rate = self.base_crossover_rate + (
                self.current_crossover_rate - self.base_crossover_rate
            ) * (1 - adjustment)
            
        # Clamp to allowed range
        return max(self.min_crossover_rate, min(self.max_crossover_rate, new_rate))
    
    def adapt_parameters(
        self,
        generation: int,
        best_fitness: float,
        avg_fitness: float,
        diversity: float
    ) -> Tuple[float, float]:
        """
        Adapt parameters based on population metrics.
        
        This is the main method to call for parameter adaptation.
        
        Args:
            generation: Current generation number
            best_fitness: Best fitness in current population
            avg_fitness: Average fitness in current population
            diversity: Current population diversity
            
        Returns:
            Tuple of (mutation_rate, crossover_rate)
        """
        # Update history tracking
        self.update_history(best_fitness, diversity)
        
        # Check if we should adapt parameters
        if not self.should_adapt(generation):
            return self.current_mutation_rate, self.current_crossover_rate
            
        # Calculate derivative metrics
        diversity_trend = self.get_diversity_trend()
        convergence_rate = self.get_convergence_rate()
        
        # Adjust parameters
        new_mutation_rate = self.adjust_mutation_rate(diversity, diversity_trend)
        new_crossover_rate = self.adjust_crossover_rate(convergence_rate, diversity)
        
        # Update current parameters
        self.current_mutation_rate = new_mutation_rate
        self.current_crossover_rate = new_crossover_rate
        self.last_adaptation_generation = generation
        
        print(f"Generation {generation}: Adaptive parameters updated")
        print(f"  Diversity: {diversity:.4f}, Trend: {diversity_trend:.4f}")
        print(f"  Convergence rate: {convergence_rate:.4f}")
        print(f"  New mutation rate: {new_mutation_rate:.4f}")
        print(f"  New crossover rate: {new_crossover_rate:.4f}")
        
        return new_mutation_rate, new_crossover_rate