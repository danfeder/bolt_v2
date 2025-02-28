"""Unified solver implementation with configurable features"""
from typing import Dict, Any, List, Optional
import traceback
from dateutil import parser
import logging

from ..core import SchedulerContext, ConstraintManager, SolverConfig
from . import config
from .config import (
    get_base_constraints,
    get_base_objectives,
    GENETIC_CONFIG,
    META_CONFIG,
    WEIGHTS
)
from ..objectives.distribution import DistributionObjective
from .base import BaseSolver
from ...models import ScheduleRequest, ScheduleResponse, WeightConfig
from .genetic.optimizer import GeneticOptimizer
from .genetic.meta_optimizer import MetaOptimizer

logger = logging.getLogger(__name__)

class UnifiedSolver(BaseSolver):
    """
    Unified solver that combines production-ready and experimental features.
    Features can be enabled/disabled through configuration.
    """
    
    def __init__(self, request: Optional[ScheduleRequest] = None, 
                config: Optional[SolverConfig] = None,
                use_or_tools: bool = True,
                use_genetic: bool = True,
                custom_weights: Optional[Dict[str, int]] = None):
        """
        Initialize the unified solver.
        
        Args:
            request: Optional schedule request for initialization
            config: Optional solver configuration
            use_or_tools: Whether to use OR-Tools CP-SAT solver
            use_genetic: Whether to use genetic algorithm
            custom_weights: Optional custom weights to override defaults
        """
        super().__init__("cp-sat-unified")
        self.request = request
        self.use_or_tools = use_or_tools
        self.use_genetic = use_genetic
        self.base_config = config
        
        # Initialize or-tools solver if needed
        if use_or_tools:
            from ortools.sat.python import cp_model
            self.model = cp_model.CpModel()
            self.solver = cp_model.CpSolver()
        else:
            self.model = None
            self.solver = None
            
        self._last_run_metadata = None
        self._last_stable_response: Optional[ScheduleResponse] = None
        self._constraint_manager = ConstraintManager()
        self.constraint_violations = []
        
        # Override weights if provided
        self.custom_weights = custom_weights
        
        # Initialize genetic optimizer if enabled
        self.genetic_optimizer = (
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
            if config.ENABLE_GENETIC_OPTIMIZATION and use_genetic
            else None
        )
        
        # Initialize meta-optimizer if enabled
        self.meta_optimizer = None
        
        # Add base constraints through constraint manager
        for constraint in get_base_constraints():
            self._constraint_manager.add_constraint(constraint)
            
        # Add base objectives
        for objective in get_base_objectives():
            self.add_objective(objective)
            
        # Add experimental distribution optimization if enabled
        if config.ENABLE_EXPERIMENTAL_DISTRIBUTION:
            self.add_objective(DistributionObjective())
            
        # Add grade grouping objective if enabled
        if config.ENABLE_GRADE_GROUPING:
            self.add_objective(GradeGroupingObjective())

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

    def get_weights(self) -> Dict[str, int]:
        """
        Get the current weights.
        
        Returns:
            Dict of objective name to weight value
        """
        if self.custom_weights:
            return self.custom_weights
        else:
            return WEIGHTS
            
    def tune_weights(self, request: ScheduleRequest = None) -> WeightConfig:
        """
        Tune weights using the meta-optimizer.
        
        Args:
            request: Schedule request to tune weights for (uses self.request if None)
            
        Returns:
            Optimized weight configuration
        """
        if not config.ENABLE_WEIGHT_TUNING:
            logger.warning("Weight tuning is disabled. Enable with ENABLE_WEIGHT_TUNING=1")
            return WeightConfig(**WEIGHTS)
            
        if not self.use_genetic:
            logger.warning("Weight tuning requires genetic algorithm. Enable with use_genetic=True")
            return WeightConfig(**WEIGHTS)
            
        req = request if request is not None else self.request
        if not req:
            raise ValueError("Schedule request is required for weight tuning")
            
        logger.info("Starting weight tuning process...")
        
        # Create meta-optimizer if not already created
        if not self.meta_optimizer:
            self.meta_optimizer = MetaOptimizer(
                request=req,
                base_config=self.base_config,
                population_size=META_CONFIG.POPULATION_SIZE,
                generations=META_CONFIG.GENERATIONS,
                mutation_rate=META_CONFIG.MUTATION_RATE,
                crossover_rate=META_CONFIG.CROSSOVER_RATE,
                eval_time_limit=META_CONFIG.EVAL_TIME_LIMIT
            )
            
        # Run meta-optimization
        best_config, best_fitness = self.meta_optimizer.optimize(
            parallel=META_CONFIG.PARALLEL_EVALUATION
        )
        
        logger.info(f"Weight tuning complete. Best fitness: {best_fitness}")
        logger.info(f"Optimized weights: {best_config}")
        
        # Update custom weights
        self.custom_weights = best_config.weights_dict
        
        return best_config
    
    def solve(self, request: ScheduleRequest = None, 
              time_limit_seconds: int = None, 
              tune_weights: bool = False) -> ScheduleResponse:
        """
        Solve the scheduling problem.
        
        Args:
            request: Schedule request to solve (uses self.request if None)
            time_limit_seconds: Time limit for solver
            tune_weights: Whether to tune weights before solving
            
        Returns:
            Schedule response with assignments
        """
        # Use provided request or stored request
        req = request if request is not None else self.request
        if not req:
            raise ValueError("Schedule request is required")
            
        # Set time limit
        time_limit = time_limit_seconds if time_limit_seconds is not None else config.SOLVER_TIME_LIMIT_SECONDS
        
        # Store request for future use
        self.request = req
        
        # Tune weights if requested
        if tune_weights and config.ENABLE_WEIGHT_TUNING:
            self.tune_weights(req)
            
        # Create schedule
        return self.create_schedule(req, time_limit)
    
    def create_schedule(self, request: ScheduleRequest, time_limit_seconds: int = None) -> ScheduleResponse:
        """Create a schedule using the unified solver configuration"""
        logger.info(f"Starting unified solver for {len(request.classes)} classes...")
        logger.info("\nSolver configuration:")
        logger.info("Feature flags:")
        logger.info(f"- Metrics enabled: {config.ENABLE_METRICS}")
        logger.info(f"- Solution comparison enabled: {config.ENABLE_SOLUTION_COMPARISON}")
        logger.info(f"- Experimental distribution enabled: {config.ENABLE_EXPERIMENTAL_DISTRIBUTION}")
        logger.info(f"- Genetic optimization enabled: {config.ENABLE_GENETIC_OPTIMIZATION}")
        logger.info(f"- Consecutive classes control enabled: {config.ENABLE_CONSECUTIVE_CLASSES}")
        logger.info(f"- Teacher breaks enabled: {config.ENABLE_TEACHER_BREAKS}")
        logger.info(f"- Weight tuning enabled: {config.ENABLE_WEIGHT_TUNING}")
        logger.info(f"- Grade grouping enabled: {config.ENABLE_GRADE_GROUPING}")
        
        if config.ENABLE_GENETIC_OPTIMIZATION and self.use_genetic:
            logger.info("\nGenetic algorithm configuration:")
            logger.info(f"- Population size: {config.GENETIC_CONFIG.POPULATION_SIZE}")
            logger.info(f"- Elite size: {config.GENETIC_CONFIG.ELITE_SIZE}")
            logger.info(f"- Max generations: {config.GENETIC_CONFIG.MAX_GENERATIONS}")
            logger.info(f"- Parallel fitness evaluation: {config.GENETIC_CONFIG.PARALLEL_FITNESS}")
            logger.info(f"- Adaptive control enabled: {config.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL}")
            if config.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL:
                logger.info(f"- Adaptation interval: {config.GENETIC_CONFIG.ADAPTATION_INTERVAL} generations")
                logger.info(f"- Diversity threshold: {config.GENETIC_CONFIG.DIVERSITY_THRESHOLD}")
                logger.info(f"- Adaptation strength: {config.GENETIC_CONFIG.ADAPTATION_STRENGTH}")
            logger.info(f"- Available crossover methods: {', '.join(config.GENETIC_CONFIG.CROSSOVER_METHODS)}")
        
        if config.ENABLE_WEIGHT_TUNING:
            logger.info("\nWeight tuning configuration:")
            logger.info(f"- Meta population size: {config.META_CONFIG.POPULATION_SIZE}")
            logger.info(f"- Meta generations: {config.META_CONFIG.GENERATIONS}")
            logger.info(f"- Evaluation time limit: {config.META_CONFIG.EVAL_TIME_LIMIT} seconds")
            logger.info(f"- Parallel evaluation: {config.META_CONFIG.PARALLEL_EVALUATION}")
            
        logger.info("\nConstraints:")
        for constraint in self.constraints:
            logger.info(f"- {constraint.name}")
        logger.info("\nObjectives:")
        for objective in self.objectives:
            logger.info(f"- {objective.name} (weight: {objective.weight})")
            
        try:
            # Validate dates
            start_date = parser.parse(request.startDate)
            end_date = parser.parse(request.endDate)
            
            # Store current solution for comparison if needed
            if config.ENABLE_SOLUTION_COMPARISON and self._last_stable_response:
                current_stable = self._last_stable_response
            
            time_limit = time_limit_seconds if time_limit_seconds is not None else config.SOLVER_TIME_LIMIT_SECONDS
            
            if config.ENABLE_GENETIC_OPTIMIZATION and self.use_genetic and self.genetic_optimizer:
                logger.info("Using genetic algorithm optimizer")
                response = self.genetic_optimizer.optimize(
                    request=request,
                    weights=self.get_weights(),
                    time_limit_seconds=time_limit
                )
            elif self.use_or_tools:
                logger.info("Using OR-Tools CP-SAT solver")
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
            else:
                raise ValueError("Neither genetic algorithm nor OR-Tools solver is enabled")
            
            # Validate solution
            logger.info("Validating constraints...")
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
            
            self.constraint_violations = violations
            
            if violations:
                logger.warning("Constraint violations found:")
                for v in violations:
                    logger.warning(f"- {v.message}")
                logger.warning(f"Schedule validation found {len(violations)} violations")
            else:
                logger.info("All constraints satisfied!")
            
            # Store metadata for metrics if enabled
            if config.ENABLE_METRICS:
                self._last_run_metadata = response.metadata
                
            # Store response for future comparison if enabled
            if config.ENABLE_SOLUTION_COMPARISON:
                self._last_stable_response = response
                
                # Compare with previous stable solution if available
                if current_stable:
                    comparison = self._compare_solutions(current_stable, response)
                    logger.info("\nSolution comparison:")
                    logger.info(f"Total differences: {comparison['assignment_differences']['total_differences']}")
                    logger.info(f"Score difference: {comparison['metric_differences']['score']}")
                    
            return response
            
        except Exception as e:
            logger.error(f"Scheduling error in unified solver: {str(e)}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
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
