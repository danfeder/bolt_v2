"""Unified solver implementation with configurable features"""
from typing import Dict, Any, List, Optional
import traceback
from dateutil import parser

from ..core import SchedulerContext, ConstraintManager
from . import config
from .config import (
    get_base_constraints,
    get_base_objectives,
    GENETIC_CONFIG
)
from ..objectives.distribution import DistributionObjective
from .base import BaseSolver
from ...models import ScheduleRequest, ScheduleResponse
from .genetic.optimizer import GeneticOptimizer

class UnifiedSolver(BaseSolver):
    """
    Unified solver that combines production-ready and experimental features.
    Features can be enabled/disabled through configuration.
    """
    
    def __init__(self):
        super().__init__("cp-sat-unified")
        # Initialize or-tools solver
        from ortools.sat.python import cp_model
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self._last_run_metadata = None
        self._last_stable_response: Optional[ScheduleResponse] = None
        self._constraint_manager = ConstraintManager()
        
        # Initialize genetic optimizer if enabled
        self._genetic_optimizer = (
            GeneticOptimizer(
                population_size=GENETIC_CONFIG.POPULATION_SIZE,
                elite_size=GENETIC_CONFIG.ELITE_SIZE,
                mutation_rate=GENETIC_CONFIG.MUTATION_RATE,
                crossover_rate=GENETIC_CONFIG.CROSSOVER_RATE,
                max_generations=GENETIC_CONFIG.MAX_GENERATIONS,
                convergence_threshold=GENETIC_CONFIG.CONVERGENCE_THRESHOLD,
                use_adaptive_control=GENETIC_CONFIG.USE_ADAPTIVE_CONTROL,
                adaptation_interval=GENETIC_CONFIG.ADAPTATION_INTERVAL,
                diversity_threshold=GENETIC_CONFIG.DIVERSITY_THRESHOLD,
                adaptation_strength=GENETIC_CONFIG.ADAPTATION_STRENGTH,
                parallel_fitness=GENETIC_CONFIG.PARALLEL_FITNESS,
                max_workers=None  # Auto-detect
            )
            if config.ENABLE_GENETIC_OPTIMIZATION
            else None
        )
        
        # Add base constraints through constraint manager
        for constraint in get_base_constraints():
            self._constraint_manager.add_constraint(constraint)
            
        # Add base objectives
        for objective in get_base_objectives():
            self.add_objective(objective)
            
        # Add experimental distribution optimization if enabled
        if config.ENABLE_EXPERIMENTAL_DISTRIBUTION:
            self.add_objective(DistributionObjective())

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from last solver run if enabled"""
        if not config.ENABLE_METRICS:
            return {"status": "Metrics disabled"}
            
        if not self._last_run_metadata:
            return {
                "status": "No runs available",
                "metrics": None
            }
            
        return {
            "status": "success",
            "metrics": {
                "duration": self._last_run_metadata.duration,
                "score": self._last_run_metadata.score,
                "solutions_found": self._last_run_metadata.solutions_found,
                "optimization_gap": self._last_run_metadata.optimization_gap,
                "distribution": self._last_run_metadata.distribution.dict() if self._last_run_metadata.distribution else None
            }
        }

    def create_schedule(self, request: ScheduleRequest) -> ScheduleResponse:
        """Create a schedule using the unified solver configuration"""
        print(f"\nStarting unified solver for {len(request.classes)} classes...")
        print("\nSolver configuration:")
        print("Feature flags:")
        print(f"- Metrics enabled: {config.ENABLE_METRICS}")
        print(f"- Solution comparison enabled: {config.ENABLE_SOLUTION_COMPARISON}")
        print(f"- Experimental distribution enabled: {config.ENABLE_EXPERIMENTAL_DISTRIBUTION}")
        print(f"- Genetic optimization enabled: {config.ENABLE_GENETIC_OPTIMIZATION}")
        print(f"- Consecutive classes control enabled: {config.ENABLE_CONSECUTIVE_CLASSES}")
        print(f"- Teacher breaks enabled: {config.ENABLE_TEACHER_BREAKS}")
        if config.ENABLE_GENETIC_OPTIMIZATION:
            print("\nGenetic algorithm configuration:")
            print(f"- Population size: {config.GENETIC_CONFIG.POPULATION_SIZE}")
            print(f"- Elite size: {config.GENETIC_CONFIG.ELITE_SIZE}")
            print(f"- Max generations: {config.GENETIC_CONFIG.MAX_GENERATIONS}")
            print(f"- Parallel fitness evaluation: {config.GENETIC_CONFIG.PARALLEL_FITNESS}")
            print(f"- Adaptive control enabled: {config.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL}")
            if config.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL:
                print(f"- Adaptation interval: {config.GENETIC_CONFIG.ADAPTATION_INTERVAL} generations")
                print(f"- Diversity threshold: {config.GENETIC_CONFIG.DIVERSITY_THRESHOLD}")
                print(f"- Adaptation strength: {config.GENETIC_CONFIG.ADAPTATION_STRENGTH}")
            print(f"- Available crossover methods: {', '.join(config.GENETIC_CONFIG.CROSSOVER_METHODS)}")
        print("\nConstraints:")
        for constraint in self.constraints:
            print(f"- {constraint.name}")
        print("\nObjectives:")
        for objective in self.objectives:
            print(f"- {objective.name} (weight: {objective.weight})")
            
        try:
            # Validate dates
            start_date = parser.parse(request.startDate)
            end_date = parser.parse(request.endDate)
            
            # Store current solution for comparison if needed
            if config.ENABLE_SOLUTION_COMPARISON and self._last_stable_response:
                current_stable = self._last_stable_response
            
            if config.ENABLE_GENETIC_OPTIMIZATION and self._genetic_optimizer:
                print("\nUsing genetic algorithm optimizer")
                response = self._genetic_optimizer.optimize(
                    request=request,
                    weights=self.get_weights(),
                    time_limit_seconds=config.SOLVER_TIME_LIMIT_SECONDS
                )
            else:
                print("\nUsing OR-Tools CP-SAT solver")
                # Create context and apply constraints
                context = SchedulerContext(
                    model=self.model,
                    solver=self.solver,
                    request=request,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Apply constraints through manager
                self._constraint_manager.apply_all(context)
                response = super().create_schedule(request)
            
            # Validate solution
            print("\nValidating constraints...")
            validation_context = SchedulerContext(
                model=None,  # Not needed for validation
                solver=None,  # Not needed for validation
                request=request,
                start_date=start_date,
                end_date=end_date
            )
            
            # Validate using constraint manager
            violations = self._constraint_manager.validate_all(
                response.assignments,
                validation_context
            )
            
            if violations:
                print("\nConstraint violations found:")
                for v in violations:
                    print(f"- {v.message}")
                raise Exception(
                    f"Schedule validation failed with {len(violations)} violations"
                )
            
            print("\nAll constraints satisfied!")
            
            # Store metadata for metrics if enabled
            if config.ENABLE_METRICS:
                self._last_run_metadata = response.metadata
                
            # Store response for future comparison if enabled
            if config.ENABLE_SOLUTION_COMPARISON:
                self._last_stable_response = response
                
                # Compare with previous stable solution if available
                if current_stable:
                    comparison = self._compare_solutions(current_stable, response)
                    print("\nSolution comparison:")
                    print(f"Total differences: {comparison['assignment_differences']['total_differences']}")
                    print(f"Score difference: {comparison['metric_differences']['score']}")
                    
            return response
            
        except Exception as e:
            print(f"Scheduling error in unified solver: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            raise

    def _compare_solutions(self, stable_response: ScheduleResponse, new_response: ScheduleResponse) -> Dict[str, Any]:
        """Compare two solutions when solution comparison is enabled"""
        if not config.ENABLE_SOLUTION_COMPARISON:
            return {"status": "Solution comparison disabled"}
            
        # Find assignments that differ between solutions
        stable_assignments = {
            (a.classId, a.date, a.timeSlot.dayOfWeek, a.timeSlot.period): a 
            for a in stable_response.assignments
        }
        new_assignments = {
            (a.classId, a.date, a.timeSlot.dayOfWeek, a.timeSlot.period): a 
            for a in new_response.assignments
        }
        
        # Calculate differences
        differences = []
        stable_keys = set(stable_assignments.keys())
        new_keys = set(new_assignments.keys())
        
        # Find assignments missing from stable
        for key in new_keys - stable_keys:
            differences.append({
                "type": "missing_in_stable",
                "classId": key[0],
                "new": new_assignments[key],
            })
        
        # Find assignments missing from new
        for key in stable_keys - new_keys:
            differences.append({
                "type": "missing_in_new",
                "classId": key[0],
                "stable": stable_assignments[key],
            })
        
        # Find assignments that differ in timing
        for key in stable_keys & new_keys:
            if (stable_assignments[key].timeSlot.dayOfWeek != new_assignments[key].timeSlot.dayOfWeek or
                stable_assignments[key].timeSlot.period != new_assignments[key].timeSlot.period):
                differences.append({
                    "type": "different_assignment",
                    "classId": key[0],
                    "stable": stable_assignments[key],
                    "new": new_assignments[key],
                })
        
        # Compare metrics
        stable_score = stable_response.metadata.distribution.totalScore if stable_response.metadata.distribution else 0
        new_score = new_response.metadata.distribution.totalScore if new_response.metadata.distribution else 0
        
        return {
            "assignment_differences": {
                "total_differences": len(differences),
                "differences": differences
            },
            "metric_differences": {
                "score": new_score - stable_score,
                "duration": new_response.metadata.duration - stable_response.metadata.duration,
                "distribution": {
                    "score_difference": new_score - stable_score,
                    "weekly_variance_difference": (
                        (new_response.metadata.distribution.weekly["variance"] if new_response.metadata.distribution else 0) -
                        (stable_response.metadata.distribution.weekly["variance"] if stable_response.metadata.distribution else 0)
                    ),
                    "average_period_spread_difference": (
                        sum(
                            new_response.metadata.distribution.daily[date]["periodSpread"] if new_response.metadata.distribution else 0
                            for date in new_response.metadata.distribution.daily
                        ) / len(new_response.metadata.distribution.daily) -
                        sum(
                            stable_response.metadata.distribution.daily[date]["periodSpread"] if stable_response.metadata.distribution else 0
                            for date in stable_response.metadata.distribution.daily
                        ) / len(stable_response.metadata.distribution.daily)
                        if stable_response.metadata.distribution and new_response.metadata.distribution
                        else 0
                    )
                }
            }
        }
