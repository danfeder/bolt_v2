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
        fitness_values = [chromosome.fitness for chromosome in population]
        
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
            fitness_values.append(chromosome.fitness)
            
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
                        reduced_data[i, 1] = chromosome.fitness  # y coordinate is fitness
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
        ax1.plot(generations, fitness_history, 'o-', color=self.color_palette[0], 
                 linewidth=2, markersize=8, label='Best Fitness')
        
        # Plot average fitness if available
        if avg_fitness_history and len(avg_fitness_history) == len(fitness_history):
            ax1.plot(generations, avg_fitness_history, 's--', color=self.color_palette[1], 
                     linewidth=2, markersize=6, label='Average Fitness')
        
        # Add labels and legend
        ax1.set_title('Fitness Evolution Over Generations', fontsize=14)
        ax1.set_xlabel('Generation', fontsize=12)
        ax1.set_ylabel('Fitness Value', fontsize=12)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Highlight best generation
        best_gen = fitness_history.index(max(fitness_history))
        ax1.axvline(x=best_gen, color='red', linestyle='--', alpha=0.5)
        ax1.text(best_gen + 0.1, fitness_history[best_gen], 
                f'Best: Gen {best_gen}', 
                color='red', fontsize=10)
        
        # Plot diversity if available
        ax2 = plt.subplot(gs[1, 0])
        if diversity_history and len(diversity_history) == len(fitness_history):
            ax2.plot(generations, diversity_history, 'o-', color=self.color_palette[2], 
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
            improvements = [fitness_history[i] - fitness_history[i-1] for i in range(1, len(fitness_history))]
            
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
                f"Starting Fitness: {fitness_history[0]:.2f}\n"
                f"Final Fitness: {fitness_history[-1]:.2f}\n"
                f"Best Fitness: {max(fitness_history):.2f} (Gen {fitness_history.index(max(fitness_history))})\n"
                f"Improvement: {fitness_history[-1] - fitness_history[0]:.2f} ({(fitness_history[-1] - fitness_history[0]) / fitness_history[0] * 100:.1f}%)"
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
        Visualize a single chromosome as a schedule.
        
        Args:
            chromosome: The chromosome to visualize
            title: Plot title
            save_path: Path to save the visualization (None for no saving)
            
        Returns:
            Matplotlib figure
        """
        # Create figure and axis
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [3, 1]})
        fig.suptitle(title, fontsize=16)
        
        # Check if chromosome has genes
        if not chromosome.genes:
            ax1.text(0.5, 0.5, "No genes found in chromosome",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax1.transAxes, fontsize=12)
            
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
        
        # Fill in the schedule grid with class assignments
        for gene in chromosome.genes:
            day_idx = gene.time_slot.dayOfWeek - 1  # Assuming 1-indexed days
            period_idx = gene.time_slot.period - 1  # Assuming 1-indexed periods
            
            # Make sure indices are within bounds
            if 0 <= day_idx < len(days) and 0 <= period_idx < len(periods):
                schedule_grid[day_idx, period_idx] = gene.class_id
        
        # Create a table for the schedule
        cell_colors = np.full_like(schedule_grid, 'white', dtype=object)
        
        # Color cells that have assignments
        for i in range(len(days)):
            for j in range(len(periods)):
                if schedule_grid[i, j]:
                    # Assign a deterministic color based on class_id
                    class_id = schedule_grid[i, j]
                    # Create a hash of the class_id to get a repeatable color
                    hash_val = sum(ord(c) for c in class_id) % 10
                    cell_colors[i, j] = self.color_palette[hash_val]
        
        # Create the schedule table
        table = ax1.table(
            cellText=schedule_grid,
            rowLabels=days,
            colLabels=periods,
            cellColours=cell_colors,
            loc='center',
            cellLoc='center'
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)  # Adjust table size
        
        # Hide axes
        ax1.axis('off')
        ax1.set_title('Class Schedule', fontsize=14)
        
        # 2. Create a fitness and constraint information panel
        ax2.axis('off')
        ax2.set_title('Chromosome Information', fontsize=14)
        
        # Add fitness value
        info_text = f"Fitness: {chromosome.fitness:.2f}\n\n"
        
        # Add class distribution information
        class_counts = Counter(gene.class_id for gene in chromosome.genes)
        info_text += "Class Distribution:\n"
        for class_id, count in class_counts.items():
            info_text += f"- {class_id}: {count}\n"
        
        # Add day distribution information
        day_counts = Counter(gene.time_slot.dayOfWeek for gene in chromosome.genes)
        info_text += "\nDay Distribution:\n"
        for day_num, count in sorted(day_counts.items()):
            day_name = days[day_num - 1] if 1 <= day_num <= len(days) else f"Day {day_num}"
            info_text += f"- {day_name}: {count}\n"
        
        # Add constraint violations if any
        if hasattr(chromosome, 'constraint_violations') and chromosome.constraint_violations:
            info_text += "\nConstraint Violations:\n"
            for violation in chromosome.constraint_violations:
                info_text += f"- {violation}\n"
        
        # Display the information
        ax2.text(0.1, 0.9, info_text, transform=ax2.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for suptitle
        
        # Save the figure if save_path is provided
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
        # Create figure with 2x2 subplots
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(2, 2, height_ratios=[3, 1])
        fig.suptitle(title, fontsize=16)
        
        # Define days and periods
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        periods = list(range(1, 9))  # Assuming 8 periods
        
        # 1. Create schedule grids for both chromosomes
        schedule_grid1 = np.zeros((len(days), len(periods)), dtype=object)
        schedule_grid2 = np.zeros((len(days), len(periods)), dtype=object)
        
        # Initialize with empty strings
        for i in range(len(days)):
            for j in range(len(periods)):
                schedule_grid1[i, j] = ""
                schedule_grid2[i, j] = ""
        
        # Fill in the schedule grids
        for gene in chromosome1.genes:
            day_idx = gene.time_slot.dayOfWeek - 1
            period_idx = gene.time_slot.period - 1
            if 0 <= day_idx < len(days) and 0 <= period_idx < len(periods):
                schedule_grid1[day_idx, period_idx] = gene.class_id
                
        for gene in chromosome2.genes:
            day_idx = gene.time_slot.dayOfWeek - 1
            period_idx = gene.time_slot.period - 1
            if 0 <= day_idx < len(days) and 0 <= period_idx < len(periods):
                schedule_grid2[day_idx, period_idx] = gene.class_id
        
        # Create color grids
        cell_colors1 = np.full_like(schedule_grid1, 'white', dtype=object)
        cell_colors2 = np.full_like(schedule_grid2, 'white', dtype=object)
        
        # Track differences for the difference grid
        diff_grid = np.zeros((len(days), len(periods)), dtype=object)
        diff_colors = np.full_like(diff_grid, 'white', dtype=object)
        
        # Process first schedule
        for i in range(len(days)):
            for j in range(len(periods)):
                if schedule_grid1[i, j]:
                    class_id = schedule_grid1[i, j]
                    hash_val = sum(ord(c) for c in class_id) % 10
                    cell_colors1[i, j] = self.color_palette[hash_val]
                    
                    # Initialize diff grid
                    diff_grid[i, j] = class_id
                    diff_colors[i, j] = cell_colors1[i, j]
        
        # Process second schedule and identify differences
        for i in range(len(days)):
            for j in range(len(periods)):
                if schedule_grid2[i, j]:
                    class_id = schedule_grid2[i, j]
                    hash_val = sum(ord(c) for c in class_id) % 10
                    cell_colors2[i, j] = self.color_palette[hash_val]
                    
                    # Compare with first schedule
                    if schedule_grid1[i, j] != schedule_grid2[i, j]:
                        diff_grid[i, j] = f"{schedule_grid1[i, j]} → {class_id}"
                        diff_colors[i, j] = 'yellow'  # Highlight differences
                    
                    # Track assignments in second but not in first
                    if not schedule_grid1[i, j]:
                        diff_grid[i, j] = f"+ {class_id}"
                        diff_colors[i, j] = 'lightgreen'
                
                # Track assignments in first but not in second
                elif schedule_grid1[i, j]:
                    diff_grid[i, j] = f"- {schedule_grid1[i, j]}"
                    diff_colors[i, j] = 'lightcoral'
        
        # 1. First chromosome schedule
        ax1 = plt.subplot(gs[0, 0])
        table1 = ax1.table(
            cellText=schedule_grid1,
            rowLabels=days,
            colLabels=periods,
            cellColours=cell_colors1,
            loc='center',
            cellLoc='center'
        )
        
        # Style the table
        table1.auto_set_font_size(False)
        table1.set_fontsize(10)
        table1.scale(1, 1.5)  # Adjust table size
        
        # Hide axes
        ax1.axis('off')
        ax1.set_title(f'Chromosome 1 (Fitness: {chromosome1.fitness:.2f})', fontsize=14)
        
        # 2. Second chromosome schedule
        ax2 = plt.subplot(gs[0, 1])
        table2 = ax2.table(
            cellText=schedule_grid2,
            rowLabels=days,
            colLabels=periods,
            cellColours=cell_colors2,
            loc='center',
            cellLoc='center'
        )
        
        # Style the table
        table2.auto_set_font_size(False)
        table2.set_fontsize(10)
        table2.scale(1, 1.5)  # Adjust table size
        
        # Hide axes
        ax2.axis('off')
        ax2.set_title(f'Chromosome 2 (Fitness: {chromosome2.fitness:.2f})', fontsize=14)
        
        # 3. Differences visualization
        ax3 = plt.subplot(gs[1, :])
        table3 = ax3.table(
            cellText=diff_grid,
            rowLabels=days,
            colLabels=periods,
            cellColours=diff_colors,
            loc='center',
            cellLoc='center'
        )
        
        # Style the table
        table3.auto_set_font_size(False)
        table3.set_fontsize(10)
        table3.scale(1, 1.5)  # Adjust table size
        
        # Hide axes
        ax3.axis('off')
        
        # Add legend for difference table
        diff_title = f'Differences (Fitness Δ: {chromosome2.fitness - chromosome1.fitness:.2f})'
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
            f"Fitness Improvement: {chromosome2.fitness - chromosome1.fitness:.2f}\n"
            f"Relative Improvement: {(chromosome2.fitness - chromosome1.fitness) / abs(chromosome1.fitness) * 100:.1f}%"
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
