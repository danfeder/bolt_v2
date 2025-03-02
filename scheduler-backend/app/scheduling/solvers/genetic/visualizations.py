"""Visualization tools for genetic algorithm populations and chromosomes."""
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import os
import json
from collections import Counter
import seaborn as sns
from datetime import datetime

from ....models import ScheduleRequest, ScheduleAssignment, TimeSlot
from ..genetic.chromosome import ScheduleChromosome, Gene
from ..genetic.population import PopulationManager


class PopulationVisualizer:
    """
    Visualizer for genetic algorithm populations.
    
    This class provides tools to visualize various aspects of the genetic algorithm
    populations including diversity, fitness landscape, population evolution, 
    and chromosome representations.
    """
    
    def __init__(self, output_dir: str = "ga_visualizations"):
        """
        Initialize the population visualizer.
        
        Args:
            output_dir: Directory to save visualization files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up plot style
        plt.style.use('ggplot')
        self.color_palette = sns.color_palette("viridis", 10)
    
    def _ensure_numeric(self, value, default=0.0):
        """Ensure a value is a numeric type, handling special cases.
        
        This handles:
        - None values
        - _NoValueType objects from unittest.mock
        - Other objects that might not be directly convertible to float
        
        Args:
            value: The value to convert to a numeric type
            default: Default value to use if conversion fails
            
        Returns:
            float: The numeric representation of the value or the default
        """
        # Handle None
        if value is None:
            return default
            
        # Handle mock objects and _NoValueType
        if hasattr(value, '__class__'):
            class_name = value.__class__.__name__
            if class_name == '_NoValueType' or 'Mock' in class_name:
                return default
        
        # Try converting to float
        try:
            return float(value)
        except (TypeError, ValueError):
            # If it's an array-like object, try to get the first element
            try:
                if hasattr(value, '__len__') and hasattr(value, '__getitem__'):
                    if len(value) > 0:
                        return float(value[0])
            except (TypeError, ValueError, IndexError):
                pass
            
            return default
        
    def visualize_diversity(
        self, 
        population: List[ScheduleChromosome],
        title: str = "Population Diversity",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize population diversity using heatmap and metrics.
        
        Args:
            population: List of chromosomes to visualize
            title: Plot title
            save_path: Path to save the visualization (None for no saving)
            
        Returns:
            Matplotlib figure
        """
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(title, fontsize=16)
        
        # Extract fitness values for distribution plot
        fitness_values = [self._ensure_numeric(chromosome.fitness) for chromosome in population]
        
        # 1. Create a fitness distribution histogram
        sns.histplot(fitness_values, kde=True, ax=ax1, color=self.color_palette[0])
        ax1.set_title("Fitness Distribution")
        ax1.set_xlabel("Fitness Value")
        ax1.set_ylabel("Count")
        
        # Add statistical annotations
        if fitness_values:
            stats_text = (
                f"Mean: {np.mean(fitness_values):.2f}\n"
                f"Median: {np.median(fitness_values):.2f}\n"
                f"Std Dev: {np.std(fitness_values):.2f}\n"
                f"Min: {min(fitness_values):.2f}\n"
                f"Max: {max(fitness_values):.2f}"
            )
            ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, 
                    fontsize=10, verticalalignment='top', 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        # 2. Create a similarity heatmap if there are enough chromosomes
        if len(population) >= 2:
            # Calculate hamming distance between chromosomes
            n_chromosomes = min(len(population), 20)  # Limit to 20 for visualization
            distance_matrix = np.zeros((n_chromosomes, n_chromosomes))
            
            # Compute distances
            for i in range(n_chromosomes):
                for j in range(n_chromosomes):
                    if i == j:
                        distance_matrix[i, j] = 0
                    else:
                        # Count different genes
                        distance = 0
                        chromosome1 = population[i]
                        chromosome2 = population[j]
                        
                        # Create dictionaries mapping class_id to time_slot for each chromosome
                        genes1 = {gene.class_id: gene.time_slot for gene in chromosome1.genes}
                        genes2 = {gene.class_id: gene.time_slot for gene in chromosome2.genes}
                        
                        # Count differences
                        for class_id in set(genes1.keys()) | set(genes2.keys()):
                            slot1 = genes1.get(class_id)
                            slot2 = genes2.get(class_id)
                            
                            if slot1 is None or slot2 is None:
                                distance += 1
                            elif slot1.dayOfWeek != slot2.dayOfWeek or slot1.period != slot2.period:
                                distance += 1
                                
                        distance_matrix[i, j] = distance
            
            # Create heatmap
            sns.heatmap(distance_matrix, annot=True, fmt=".0f", ax=ax2, cmap="viridis")
            ax2.set_title("Chromosome Similarity (Hamming Distance)")
            ax2.set_xlabel("Chromosome Index")
            ax2.set_ylabel("Chromosome Index")
        else:
            # Not enough chromosomes for meaningful comparison
            ax2.text(0.5, 0.5, "Insufficient chromosomes for similarity analysis",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax2.transAxes, fontsize=12)
            ax2.set_title("Chromosome Similarity")
        
        plt.tight_layout()
        
        # Save the figure if save_path is provided
        if save_path:
            self._save_figure(fig, save_path)
            
        return fig
        
    def visualize_fitness_landscape(
        self,
        population: List[ScheduleChromosome],
        dimension_reducer=None,
        title: str = "Fitness Landscape",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize the fitness landscape using dimensionality reduction.
        
        Args:
            population: List of chromosomes to visualize
            dimension_reducer: Custom dimensionality reduction function (optional)
            title: Plot title
            save_path: Path to save the visualization (None for no saving)
            
        Returns:
            Matplotlib figure
        """
        # Check if we have enough chromosomes
        if len(population) < 3:
            # Create simple figure with message
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Insufficient chromosomes for fitness landscape analysis (need at least 3)",
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(title)
            
            if save_path:
                self._save_figure(fig, save_path)
                
            return fig
        
        # Extract chromosome features and fitness values
        # We'll encode chromosomes as feature vectors
        feature_vectors = []
        fitness_values = []
        
        for chromosome in population:
            # Create a feature representation of the chromosome
            genes_dict = {}
            for gene in chromosome.genes:
                # Create a feature encoding the class assignment
                # Format: "class_{id}_day_{day}_period_{period}"
                feature_key = f"class_{gene.class_id}_day_{gene.time_slot.dayOfWeek}_period_{gene.time_slot.period}"
                genes_dict[feature_key] = 1
            
            # Add the chromosome's fitness
            fitness_values.append(self._ensure_numeric(chromosome.fitness))
            
            # Add the chromosome's feature vector
            feature_vectors.append(genes_dict)
        
        # Create a DataFrame from feature vectors
        df = pd.DataFrame(feature_vectors).fillna(0)
        
        # Apply dimension reduction if we have more than 2 features
        if df.shape[1] > 2:
            if dimension_reducer is not None:
                # Use provided dimension reducer
                reduced_data = dimension_reducer(df.values)
            else:
                # Use PCA as default
                from sklearn.decomposition import PCA
                
                # If available, use PCA for dimensionality reduction
                try:
                    pca = PCA(n_components=2)
                    reduced_data = pca.fit_transform(df.values)
                except ImportError:
                    # If sklearn is not available, use a simple approach
                    # Just select the first two principal components
                    reduced_data = np.zeros((len(population), 2))
                    for i, chromosome in enumerate(population):
                        reduced_data[i, 0] = i % 10  # Simple x coordinate
                        reduced_data[i, 1] = self._ensure_numeric(chromosome.fitness)  # y coordinate is fitness
        else:
            # Use the original data if it already has 2 or fewer dimensions
            reduced_data = df.values
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create scatter plot with fitness as color
        scatter = ax.scatter(
            reduced_data[:, 0], 
            reduced_data[:, 1],
            c=fitness_values, 
            cmap='viridis', 
            s=100,
            alpha=0.7
        )
        
        # Add color bar
        cbar = plt.colorbar(scatter)
        cbar.set_label('Fitness Value')
        
        # Label the points with their index or fitness
        for i, (x, y) in enumerate(zip(reduced_data[:, 0], reduced_data[:, 1])):
            ax.annotate(
                f"{i}",
                (x, y),
                textcoords="offset points",
                xytext=(0, 5),
                ha='center'
            )
        
        # Add title and labels
        ax.set_title(title)
        ax.set_xlabel('Dimension 1')
        ax.set_ylabel('Dimension 2')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add fitness statistics as text box
        if fitness_values:
            stats_text = (
                f"Best Fitness: {max(fitness_values):.2f}\n"
                f"Mean Fitness: {np.mean(fitness_values):.2f}\n"
                f"Worst Fitness: {min(fitness_values):.2f}\n"
                f"Std Dev: {np.std(fitness_values):.2f}"
            )
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.tight_layout()
        
        # Save the figure if save_path is provided
        if save_path:
            self._save_figure(fig, save_path)
            
        return fig
        
    def visualize_population_evolution(
        self,
        fitness_history: List[float],
        avg_fitness_history: List[float],
        diversity_history: List[float],
        title: str = "Population Evolution",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize how population statistics evolve over generations.
        
        Args:
            fitness_history: History of best fitness values per generation
            avg_fitness_history: History of average fitness values per generation
            diversity_history: History of population diversity per generation
            title: Plot title
            save_path: Path to save the visualization (None for no saving)
            
        Returns:
            Matplotlib figure
        """
        # Ensure inputs are lists or convert them safely
        try:
            if hasattr(fitness_history, 'tolist'):
                fitness_history = fitness_history.tolist()
            else:
                fitness_history = list(fitness_history or [])
        except (TypeError, ValueError):
            fitness_history = []
            
        try:
            if hasattr(avg_fitness_history, 'tolist'):
                avg_fitness_history = avg_fitness_history.tolist()
            else:
                avg_fitness_history = list(avg_fitness_history or [])
        except (TypeError, ValueError):
            avg_fitness_history = []
            
        try:
            if hasattr(diversity_history, 'tolist'):
                diversity_history = diversity_history.tolist()
            else:
                diversity_history = list(diversity_history or [])
        except (TypeError, ValueError):
            diversity_history = []
            
        # Convert all values to ensure they are numeric
        fitness_history = [self._ensure_numeric(val) for val in fitness_history]
        avg_fitness_history = [self._ensure_numeric(val) for val in avg_fitness_history]
        diversity_history = [self._ensure_numeric(val) for val in diversity_history]
        
        # Validate inputs
        if not fitness_history or len(fitness_history) < 2:
            # Not enough data to plot evolution
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Insufficient data for population evolution analysis (need at least 2 generations)",
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(title)
            
            if save_path:
                self._save_figure(fig, save_path)
                
            return fig
        
        # Create figure with subplots
        fig = plt.figure(figsize=(14, 8))
        gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1])
        
        # Main plot for fitness over generations
        ax1 = plt.subplot(gs[0, :])
        
        # Generation numbers (x-axis)
        generations = list(range(len(fitness_history)))
        
        # Plot best fitness
        ax1.plot(generations, [self._ensure_numeric(f) for f in fitness_history], 'o-', color=self.color_palette[0], 
                 linewidth=2, markersize=8, label='Best Fitness')
        
        # Plot average fitness if available
        if avg_fitness_history and len(avg_fitness_history) == len(fitness_history):
            ax1.plot(generations, [self._ensure_numeric(f) for f in avg_fitness_history], 's--', color=self.color_palette[1], 
                     linewidth=2, markersize=6, label='Average Fitness')
        
        # Add labels and legend
        ax1.set_title('Fitness Evolution Over Generations', fontsize=14)
        ax1.set_xlabel('Generation', fontsize=12)
        ax1.set_ylabel('Fitness Value', fontsize=12)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Highlight best generation
        best_gen = [self._ensure_numeric(f) for f in fitness_history].index(max([self._ensure_numeric(f) for f in fitness_history]))
        ax1.axvline(x=best_gen, color='red', linestyle='--', alpha=0.5)
        ax1.text(best_gen + 0.1, max([self._ensure_numeric(f) for f in fitness_history]), 
                f'Best: Gen {best_gen}', 
                color='red', fontsize=10)
        
        # Plot diversity if available
        ax2 = plt.subplot(gs[1, 0])
        if diversity_history and len(diversity_history) == len(fitness_history):
            ax2.plot(generations, [self._ensure_numeric(d) for d in diversity_history], 'o-', color=self.color_palette[2], 
                     linewidth=2, markersize=6)
            ax2.set_title('Population Diversity', fontsize=12)
            ax2.set_xlabel('Generation', fontsize=10)
            ax2.set_ylabel('Diversity', fontsize=10)
            ax2.grid(True, linestyle='--', alpha=0.7)
        else:
            ax2.text(0.5, 0.5, "No diversity data available",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax2.transAxes, fontsize=10)
            ax2.set_title('Population Diversity', fontsize=12)
        
        # Plot fitness improvement rate
        ax3 = plt.subplot(gs[1, 1])
        if len(fitness_history) >= 3:
            # Calculate improvement rate (derivative of fitness)
            improvements = [self._ensure_numeric(fitness_history[i]) - self._ensure_numeric(fitness_history[i-1]) for i in range(1, len(fitness_history))]
            
            # Plot improvement rate
            ax3.bar(generations[1:], improvements, color=self.color_palette[3], alpha=0.7)
            ax3.set_title('Fitness Improvement Rate', fontsize=12)
            ax3.set_xlabel('Generation', fontsize=10)
            ax3.set_ylabel('Improvement', fontsize=10)
            ax3.grid(True, linestyle='--', alpha=0.7)
            
            # Add horizontal line at y=0
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        else:
            ax3.text(0.5, 0.5, "Insufficient data for improvement analysis",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax3.transAxes, fontsize=10)
            ax3.set_title('Fitness Improvement Rate', fontsize=12)
        
        # Add summary statistics
        if fitness_history:
            stats_text = (
                f"Starting Fitness: {self._ensure_numeric(fitness_history[0]):.2f}\n"
                f"Final Fitness: {self._ensure_numeric(fitness_history[-1]):.2f}\n"
                f"Best Fitness: {max([self._ensure_numeric(f) for f in fitness_history]):.2f} (Gen {best_gen})\n"
                f"Improvement: {self._ensure_numeric(fitness_history[-1]) - self._ensure_numeric(fitness_history[0]):.2f} ({(self._ensure_numeric(fitness_history[-1]) - self._ensure_numeric(fitness_history[0])) / abs(self._ensure_numeric(fitness_history[0])) * 100:.1f}%)"
            )
            ax1.text(0.02, 0.02, stats_text, transform=ax1.transAxes, 
                   fontsize=10, verticalalignment='bottom', 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        # Add overall title
        plt.suptitle(title, fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for suptitle
        
        # Save the figure if save_path is provided
        if save_path:
            self._save_figure(fig, save_path)
            
        return fig
        
    def visualize_chromosome(
        self,
        chromosome: ScheduleChromosome,
        title: str = "Chromosome Visualization",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize a chromosome as a schedule.
        
        Args:
            chromosome: Schedule chromosome to visualize
            title: Plot title
            save_path: Path to save the visualization (None for no saving)
            
        Returns:
            Matplotlib figure
        """
        # Handle case where chromosome might be None
        if chromosome is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No chromosome provided for visualization",
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12)
            ax.set_title(title)
            if save_path:
                self._save_figure(fig, save_path)
            return fig
        
        # Create figure and axis
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [3, 1]})
        fig.suptitle(title, fontsize=16)
        
        # Handle empty genes case
        if not hasattr(chromosome, 'genes') or not chromosome.genes:
            ax1.text(0.5, 0.5, "Chromosome has no assignments to visualize",
                horizontalalignment='center', verticalalignment='center',
                transform=ax1.transAxes, fontsize=12)
            
            # Add fitness information on the right panel
            fitness_value = self._ensure_numeric(getattr(chromosome, 'fitness', None))
            fitness_text = f"Fitness: {fitness_value:.2f}" if fitness_value is not None else "Fitness: N/A"
            
            ax2.text(0.5, 0.5, fitness_text,
                horizontalalignment='center', verticalalignment='center',
                transform=ax2.transAxes, fontsize=12)
                
            ax1.set_title('Class Schedule', fontsize=14)
            ax2.set_title('Chromosome Information', fontsize=14)
            
            # Hide axes
            ax1.axis('off')
            ax2.axis('off')
            
            if save_path:
                self._save_figure(fig, save_path)
                
            return fig
        
        # 1. Create a schedule grid visualization
        
        # Define days and periods
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        periods = list(range(1, 9))  # Assuming 8 periods
        
        # Create empty schedule grid
        schedule_grid = np.zeros((len(days), len(periods)), dtype=object)
        for i in range(len(days)):
            for j in range(len(periods)):
                schedule_grid[i, j] = ""
        
        # Create a cell colors matrix
        cell_colors = np.zeros((len(days), len(periods)), dtype=object)
        for i in range(len(days)):
            for j in range(len(periods)):
                cell_colors[i, j] = 'white'  # Default color
        
        # Fill in the schedule grid with class assignments
        for gene in chromosome.genes:
            # Get the day and period from the gene
            # First try to use time_slot property if available
            try:
                if hasattr(gene, 'time_slot'):
                    day_idx = days.index(gene.time_slot.dayOfWeek)
                    period_idx = periods.index(gene.time_slot.period)
                else:
                    # Fall back to using day_of_week and period directly
                    day_idx = gene.day_of_week - 1  # Convert from 1-indexed to 0-indexed
                    period_idx = gene.period - 1    # Convert from 1-indexed to 0-indexed
                
                # Add the class to the grid
                class_name = ""
                if hasattr(gene, 'class_obj') and hasattr(gene.class_obj, 'name'):
                    class_name = gene.class_obj.name
                elif hasattr(gene, 'class_id'):
                    class_name = gene.class_id
                else:
                    class_name = "Unknown"
                    
                schedule_grid[day_idx, period_idx] = class_name
                
                # Set a color based on class name (for visual distinction)
                hash_val = hash(class_name) % len(self.color_palette)
                cell_colors[day_idx, period_idx] = self.color_palette[hash_val]
            except (ValueError, IndexError, AttributeError) as e:
                # Skip if there's an error with the gene
                continue
        
        # Create the schedule table
        table = ax1.table(
            cellText=schedule_grid,
            rowLabels=days,
            colLabels=periods,
            cellColours=cell_colors,
            loc='center'
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.auto_set_column_width(col=list(range(len(periods))))
        table.scale(1, 1.5)  # Adjust table size
        
        # Hide axes
        ax1.axis('off')
        ax1.set_title('Class Schedule', fontsize=14)
        
        # 2. Create a fitness and constraint information panel
        ax2.axis('off')
        ax2.set_title('Chromosome Information', fontsize=14)
        
        # Add fitness value 
        info_text = f"Fitness: {self._ensure_numeric(getattr(chromosome, 'fitness', 0.0)):.2f}\n\n"
        
        # Add class distribution information
        class_counts = {}
        for gene in chromosome.genes:
            if hasattr(gene, 'class_obj') and hasattr(gene.class_obj, 'name'):
                class_name = gene.class_obj.name
            elif hasattr(gene, 'class_id'):
                class_name = gene.class_id
            else:
                class_name = "Unknown"
                
            if class_name in class_counts:
                class_counts[class_name] += 1
            else:
                class_counts[class_name] = 1
        
        info_text += "Class Distribution:\n"
        for cls, count in class_counts.items():
            info_text += f"- {cls}: {count}\n"
        
        # Add constraint violations if available
        constraint_violations = getattr(chromosome, 'constraint_violations', [])
        if constraint_violations:
            info_text += "\nConstraint Violations:\n"
            for violation in constraint_violations:
                info_text += f"- {violation}\n"
        
        # Display the information
        ax2.text(0.1, 0.9, info_text, transform=ax2.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        # Add tight layout and save if needed
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for suptitle
        
        if save_path:
            self._save_figure(fig, save_path)
            
        return fig
        
    def visualize_chromosome_comparison(
        self,
        chromosome1: ScheduleChromosome,
        chromosome2: ScheduleChromosome,
        title: str = "Chromosome Comparison",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize a comparison between two chromosomes.
        
        Args:
            chromosome1: First chromosome to compare
            chromosome2: Second chromosome to compare
            title: Plot title
            save_path: Path to save the visualization (None for no saving)
            
        Returns:
            Matplotlib figure
        """
        # Handle case where either chromosome is None
        if chromosome1 is None or chromosome2 is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Cannot compare chromosomes: One or both chromosomes are missing",
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(title)
            if save_path:
                self._save_figure(fig, save_path)
            return fig
            
        # Handle case where both chromosomes have no genes
        if (not hasattr(chromosome1, 'genes') or not chromosome1.genes) and \
           (not hasattr(chromosome2, 'genes') or not chromosome2.genes):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Both chromosomes have no assignments to compare",
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(title)
            if save_path:
                self._save_figure(fig, save_path)
            return fig
        
        # Create figure with 3 subplots (1st chromosome, 2nd chromosome, differences)
        fig, axes = plt.subplots(1, 3, figsize=(20, 8), gridspec_kw={'width_ratios': [2, 2, 3]})
        fig.suptitle(title, fontsize=16)
        
        # Define day name map
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # Helper function to convert numeric day to name
        def day_number_to_name(day_num):
            # 1-indexed day numbers (where 1 = Monday)
            if 1 <= day_num <= 5:
                return day_names[day_num-1]
            return f"Day {day_num}"  # Fallback
        
        # Create empty schedule grids
        schedule_grid1 = np.zeros((len(day_names), 8), dtype=object)  # Assuming 8 periods
        schedule_grid2 = np.zeros((len(day_names), 8), dtype=object)
        diff_grid = np.zeros((len(day_names), 8), dtype=object)
        
        for i in range(len(day_names)):
            for j in range(8):  # Assuming 8 periods
                schedule_grid1[i, j] = ""
                schedule_grid2[i, j] = ""
                diff_grid[i, j] = ""
        
        # Create cell color matrices
        cell_colors1 = np.full_like(schedule_grid1, 'white', dtype=object)
        cell_colors2 = np.full_like(schedule_grid2, 'white', dtype=object)
        diff_colors = np.full_like(diff_grid, 'white', dtype=object)
        
        # Fill in the schedule grids
        for gene in chromosome1.genes if hasattr(chromosome1, 'genes') else []:
            try:
                # Get day and period, handling both possible structures
                if hasattr(gene, 'time_slot'):
                    day = gene.time_slot.dayOfWeek
                    # If day is a string, convert to index
                    if isinstance(day, str):
                        day_idx = day_names.index(day)
                    else:
                        day_idx = day - 1  # 1-indexed to 0-indexed
                    
                    period = gene.time_slot.period
                    # If period is a string, convert to index
                    if isinstance(period, str):
                        period_idx = int(period) - 1
                    else:
                        period_idx = period - 1  # 1-indexed to 0-indexed
                else:
                    # Use day_of_week and period directly
                    day_idx = gene.day_of_week - 1  # 1-indexed to 0-indexed
                    period_idx = gene.period - 1    # 1-indexed to 0-indexed
                
                # Get class ID or name
                if hasattr(gene, 'class_obj') and hasattr(gene.class_obj, 'name'):
                    class_id = gene.class_obj.name
                elif hasattr(gene, 'class_id'):
                    class_id = gene.class_id
                else:
                    class_id = "Unknown"
                    
                if 0 <= day_idx < len(day_names) and 0 <= period_idx < 8:
                    schedule_grid1[day_idx, period_idx] = class_id
                
                    # Set color
                    hash_val = hash(class_id) % len(self.color_palette)
                    cell_colors1[day_idx, period_idx] = self.color_palette[hash_val]
            except (ValueError, IndexError, AttributeError) as e:
                # Skip if there's an error with the gene
                continue
        
        for gene in chromosome2.genes if hasattr(chromosome2, 'genes') else []:
            try:
                # Get day and period, handling both possible structures
                if hasattr(gene, 'time_slot'):
                    day = gene.time_slot.dayOfWeek
                    # If day is a string, convert to index
                    if isinstance(day, str):
                        day_idx = day_names.index(day)
                    else:
                        day_idx = day - 1  # 1-indexed to 0-indexed
                    
                    period = gene.time_slot.period
                    # If period is a string, convert to index
                    if isinstance(period, str):
                        period_idx = int(period) - 1
                    else:
                        period_idx = period - 1  # 1-indexed to 0-indexed
                else:
                    # Use day_of_week and period directly
                    day_idx = gene.day_of_week - 1  # 1-indexed to 0-indexed
                    period_idx = gene.period - 1    # 1-indexed to 0-indexed
                
                # Get class ID or name
                if hasattr(gene, 'class_obj') and hasattr(gene.class_obj, 'name'):
                    class_id = gene.class_obj.name
                elif hasattr(gene, 'class_id'):
                    class_id = gene.class_id
                else:
                    class_id = "Unknown"
                
                if 0 <= day_idx < len(day_names) and 0 <= period_idx < 8:
                    schedule_grid2[day_idx, period_idx] = class_id
                
                    # Set color
                    hash_val = hash(class_id) % len(self.color_palette)
                    cell_colors2[day_idx, period_idx] = self.color_palette[hash_val]
            except (ValueError, IndexError, AttributeError) as e:
                # Skip if there's an error with the gene
                continue
        
        # Create tables
        ax1 = axes[0]
        table1 = ax1.table(
            cellText=schedule_grid1,
            rowLabels=day_names,
            colLabels=list(range(1, 9)),  # Assuming 8 periods
            cellColours=cell_colors1,
            loc='center',
            cellLoc='center'
        )
        
        ax2 = axes[1]
        table2 = ax2.table(
            cellText=schedule_grid2,
            rowLabels=day_names,
            colLabels=list(range(1, 9)),  # Assuming 8 periods
            cellColours=cell_colors2,
            loc='center',
            cellLoc='center'
        )
        
        ax3 = axes[2]
        table3 = ax3.table(
            cellText=diff_grid,
            rowLabels=day_names,
            colLabels=list(range(1, 9)),  # Assuming 8 periods
            cellColours=diff_colors,
            loc='center',
            cellLoc='center'
        )
        
        # Style tables
        table1.auto_set_font_size(False)
        table1.set_fontsize(10)
        table1.scale(1, 1.5)  # Adjust table size
        
        table2.auto_set_font_size(False)
        table2.set_fontsize(10)
        table2.scale(1, 1.5)  # Adjust table size
        
        table3.auto_set_font_size(False)
        table3.set_fontsize(10)
        table3.scale(1, 1.5)  # Adjust table size
        
        # Hide axes
        ax1.axis('off')
        ax2.axis('off')
        ax3.axis('off')
        
        # Set titles
        ax1.set_title(f'Chromosome 1 (Fitness: {self._ensure_numeric(chromosome1.fitness):.2f})', fontsize=14)
        ax2.set_title(f'Chromosome 2 (Fitness: {self._ensure_numeric(chromosome2.fitness):.2f})', fontsize=14)
        
        # Calculate differences
        for i in range(len(day_names)):
            for j in range(8):  # Assuming 8 periods
                if schedule_grid1[i, j] != schedule_grid2[i, j]:
                    diff_grid[i, j] = f"{schedule_grid1[i, j]} → {schedule_grid2[i, j]}"
                    diff_colors[i, j] = 'yellow'  # Highlight differences
                elif schedule_grid1[i, j] == "":
                    diff_grid[i, j] = f"+ {schedule_grid2[i, j]}"
                    diff_colors[i, j] = 'lightgreen'
                elif schedule_grid2[i, j] == "":
                    diff_grid[i, j] = f"- {schedule_grid1[i, j]}"
                    diff_colors[i, j] = 'lightcoral'
        
        # Update table 3 with differences
        table3 = ax3.table(
            cellText=diff_grid,
            rowLabels=day_names,
            colLabels=list(range(1, 9)),  # Assuming 8 periods
            cellColours=diff_colors,
            loc='center',
            cellLoc='center'
        )
        
        # Style table 3
        table3.auto_set_font_size(False)
        table3.set_fontsize(10)
        table3.scale(1, 1.5)  # Adjust table size
        
        # Add legend for difference table
        diff_title = f'Differences (Fitness Δ: {self._ensure_numeric(chromosome2.fitness) - self._ensure_numeric(chromosome1.fitness):.2f})'
        ax3.set_title(diff_title, fontsize=14)
        
        # Add a legend explaining colors
        legend_text = (
            "Yellow: Changed Assignment\n"
            "Green: Added Assignment\n"
            "Red: Removed Assignment"
        )
        ax3.text(0.02, 0.02, legend_text, transform=ax3.transAxes, 
                fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        # Calculate and display statistics
        diff_stats = (
            f"Total Changes: {np.sum(diff_colors != 'white')}\n"
            f"Fitness Improvement: {self._ensure_numeric(chromosome2.fitness) - self._ensure_numeric(chromosome1.fitness):.2f}\n"
            f"Relative Improvement: {(self._ensure_numeric(chromosome2.fitness) - self._ensure_numeric(chromosome1.fitness)) / abs(self._ensure_numeric(chromosome1.fitness)) * 100:.1f}%"
        )
        ax3.text(0.98, 0.02, diff_stats, transform=ax3.transAxes, 
                fontsize=10, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for suptitle
        
        # Save the figure if save_path is provided
        if save_path:
            self._save_figure(fig, save_path)
            
        return fig
        
    def _save_figure(self, fig: plt.Figure, save_path: Optional[str]) -> None:
        """
        Save a figure if a save path is provided.
        
        Args:
            fig: Figure to save
            save_path: Path to save the figure to
        """
        if save_path:
            full_path = os.path.join(self.output_dir, save_path)
            fig.savefig(full_path, dpi=300, bbox_inches='tight')
            print(f"Saved visualization to {full_path}")


class ChromosomeEncoder:
    """
    Encoder for converting chromosomes to visualizable formats.
    
    This class provides utilities for encoding chromosomes into formats 
    that are easier to visualize, such as adjacency matrices, distance
    matrices, or feature vectors.
    """
    
    @staticmethod
    def chromosome_to_assignment_matrix(
        chromosome: ScheduleChromosome,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Convert a chromosome to a class-timeslot assignment matrix.
        
        Args:
            chromosome: The chromosome to convert
            normalize: Whether to normalize values to [0,1] range
            
        Returns:
            2D numpy array where rows are classes and columns are timeslots
        """
        if not chromosome.genes:
            return np.array([])
        
        # Get all unique class IDs
        class_ids = sorted(set(gene.class_id for gene in chromosome.genes))
        
        # Get all unique time slots
        time_slots = []
        for gene in chromosome.genes:
            slot = (gene.time_slot.dayOfWeek, gene.time_slot.period)
            if slot not in time_slots:
                time_slots.append(slot)
        time_slots.sort()
        
        # Create assignment matrix
        matrix = np.zeros((len(class_ids), len(time_slots)))
        
        # Fill matrix with assignments
        for gene in chromosome.genes:
            class_idx = class_ids.index(gene.class_id)
            slot = (gene.time_slot.dayOfWeek, gene.time_slot.period)
            slot_idx = time_slots.index(slot)
            matrix[class_idx, slot_idx] = 1
        
        # Normalize if requested
        if normalize and np.max(matrix) > 0:
            matrix = matrix / np.max(matrix)
            
        return matrix
        
    @staticmethod
    def chromosome_to_distance_matrix(
        chromosome1: ScheduleChromosome,
        chromosome2: ScheduleChromosome
    ) -> np.ndarray:
        """
        Calculate distance matrix between two chromosomes.
        
        Args:
            chromosome1: First chromosome
            chromosome2: Second chromosome
            
        Returns:
            2D numpy array of distances between genes
        """
        if not chromosome1.genes or not chromosome2.genes:
            return np.array([])
        
        # Get all class IDs from both chromosomes
        class_ids = sorted(set(
            [gene.class_id for gene in chromosome1.genes] + 
            [gene.class_id for gene in chromosome2.genes]
        ))
        
        # Create distance matrix
        n_classes = len(class_ids)
        distance_matrix = np.zeros((n_classes, n_classes))
        
        # Create dictionaries mapping class_id to time_slot for each chromosome
        slots1 = {gene.class_id: gene.time_slot for gene in chromosome1.genes}
        slots2 = {gene.class_id: gene.time_slot for gene in chromosome2.genes}
        
        # Calculate distances
        for i, class_id1 in enumerate(class_ids):
            for j, class_id2 in enumerate(class_ids):
                # Get time slots
                slot1 = slots1.get(class_id1)
                slot2 = slots2.get(class_id2)
                
                # Calculate distance
                if slot1 is None or slot2 is None:
                    # If any class is not scheduled in a chromosome, set max distance
                    distance_matrix[i, j] = 10
                else:
                    # Calculate Euclidean distance between time slots
                    # Convert day (1-5) and period (1-8) to a 2D coordinate
                    day_diff = abs(slot1.dayOfWeek - slot2.dayOfWeek)
                    period_diff = abs(slot1.period - slot2.period)
                    
                    # Use Euclidean distance
                    distance_matrix[i, j] = np.sqrt(day_diff**2 + period_diff**2)
        
        return distance_matrix
