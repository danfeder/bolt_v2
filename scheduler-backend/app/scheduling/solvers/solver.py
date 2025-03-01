"""Unified solver implementation with configurable features"""
from typing import Dict, Any, List, Optional, Union, Type
import traceback
import os
from dateutil import parser
import logging

# Set up logger
logger = logging.getLogger(__name__)

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
from ..objectives.grade_grouping import GradeGroupingObjective
from .base import BaseSolver
from ...models import ScheduleRequest, ScheduleResponse, WeightConfig
from .genetic.optimizer import GeneticOptimizer
from .genetic.meta_optimizer import MetaOptimizer
from ..constraints.relaxation import (
    RelaxationController, 
    RelaxationLevel, 
    RelaxableConstraint,
    RelaxationResult
)

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
                custom_weights: Optional[Dict[str, int]] = None,
                enable_relaxation: Optional[bool] = None):
        """
        Initialize the unified solver.
        
        Args:
            request: Optional schedule request for initialization
            config: Optional solver configuration
            use_or_tools: Whether to use OR-Tools CP-SAT solver
            use_genetic: Whether to use genetic algorithm
            custom_weights: Optional custom weights to override defaults
            enable_relaxation: Whether to enable constraint relaxation
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
        
        # Import config module directly for defaults
        from . import config as config_module
        
        # Relaxation control
        self.enable_relaxation = (
            enable_relaxation if enable_relaxation is not None 
            else config_module.ENABLE_CONSTRAINT_RELAXATION
        )
        self.relaxation_controller = RelaxationController() if self.enable_relaxation else None
        self.current_relaxation_level = RelaxationLevel.NONE
        self.relaxation_results: List[RelaxationResult] = []
        
        # Override weights if provided
        self.custom_weights = custom_weights
        
        # Initialize genetic optimizer if enabled
        self.genetic_optimizer = None
        if config_module.ENABLE_GENETIC_OPTIMIZATION and use_genetic:
            # When running in test environment, we want to disable parallel processing
            # to avoid issues with pickling and multiprocessing
            is_test_env = 'PYTEST_CURRENT_TEST' in os.environ
            
            self.genetic_optimizer = GeneticOptimizer(
                population_size=config_module.GENETIC_CONFIG.POPULATION_SIZE,
                elite_size=config_module.GENETIC_CONFIG.ELITE_SIZE,
                mutation_rate=config_module.GENETIC_CONFIG.MUTATION_RATE,
                crossover_rate=config_module.GENETIC_CONFIG.CROSSOVER_RATE,
                max_generations=config_module.GENETIC_CONFIG.MAX_GENERATIONS,
                convergence_threshold=config_module.GENETIC_CONFIG.CONVERGENCE_THRESHOLD,
                use_adaptive_control=config_module.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL,
                adaptation_interval=config_module.GENETIC_CONFIG.ADAPTATION_INTERVAL,
                diversity_threshold=config_module.GENETIC_CONFIG.DIVERSITY_THRESHOLD,
                adaptation_strength=config_module.GENETIC_CONFIG.ADAPTATION_STRENGTH,
                # Disable parallel fitness in test environment
                parallel_fitness=False if is_test_env else config_module.GENETIC_CONFIG.PARALLEL_FITNESS,
                max_workers=1 if is_test_env else None  # Single worker in test environment
            )
        
        # Initialize meta-optimizer if enabled
        self.meta_optimizer = None
        
        # Add base constraints through constraint manager
        base_constraints = get_base_constraints()
        for constraint in base_constraints:
            self._constraint_manager.add_constraint(constraint)
            
            # Register relaxable constraints with the controller
            if self.enable_relaxation and isinstance(constraint, RelaxableConstraint):
                self.relaxation_controller.register_constraint(constraint)
            
        # Add base objectives
        for objective in get_base_objectives():
            self.add_objective(objective)
            
        # Add experimental distribution optimization if enabled
        if config_module.ENABLE_EXPERIMENTAL_DISTRIBUTION:
            self.add_objective(DistributionObjective())
            
        # Add grade grouping objective if enabled
        if config_module.ENABLE_GRADE_GROUPING:
            self.add_objective(GradeGroupingObjective())

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from last solver run if enabled"""
        from . import config as config_module
        if not config_module.ENABLE_METRICS:
            return {"status": "Metrics disabled"}
            
        if not self._last_run_metadata:
            return {
                "status": "No runs available",
                "metrics": None
            }
            
        return {
            "status": "success",
            "metrics": {
                "duration": self._last_run_metadata.duration_ms,
                "score": self._last_run_metadata.score,
                "solutions_found": self._last_run_metadata.solutions_found,
                "optimization_gap": self._last_run_metadata.gap,
                "distribution": self._last_run_metadata.distribution.dict() if self._last_run_metadata.distribution else None
            }
        }

    def get_weights(self) -> Dict[str, int]:
        """
        Get the current weights.
        
        Returns:
            Dict of objective name to weight value
        """
        from . import config as config_module
        if self.custom_weights:
            return self.custom_weights
        else:
            return config_module.WEIGHTS
            
    def tune_weights(self, request: ScheduleRequest = None) -> WeightConfig:
        """
        Tune weights using the meta-optimizer.
        
        Args:
            request: Schedule request to tune weights for (uses self.request if None)
            
        Returns:
            Optimized weight configuration
        """
        from . import config as config_module
        if not config_module.ENABLE_WEIGHT_TUNING:
            logger.warning("Weight tuning is disabled. Enable with ENABLE_WEIGHT_TUNING=1")
            return WeightConfig(**config_module.WEIGHTS)
            
        if not self.use_genetic:
            logger.warning("Weight tuning requires genetic algorithm. Enable with use_genetic=True")
            return WeightConfig(**config_module.WEIGHTS)
            
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
    
    def relax_constraints(
        self, 
        level: Union[RelaxationLevel, str, int],
        context: Optional[SchedulerContext] = None
    ) -> List[RelaxationResult]:
        """
        Relax constraints to the specified level.
        
        Args:
            level: Relaxation level to apply (can be RelaxationLevel enum, 
                  string name, or int value 0-4)
            context: Optional scheduler context for reference
            
        Returns:
            List of relaxation results
        """
        if not self.enable_relaxation or not self.relaxation_controller:
            logger.warning("Constraint relaxation is disabled")
            return []
            
        # Convert level to RelaxationLevel enum if needed
        if isinstance(level, str):
            try:
                level = RelaxationLevel[level.upper()]
            except KeyError:
                raise ValueError(f"Invalid relaxation level name: {level}")
        elif isinstance(level, int):
            try:
                level = RelaxationLevel(level)
            except ValueError:
                raise ValueError(f"Invalid relaxation level value: {level}")
                
        # Store current level
        self.current_relaxation_level = level
        
        # Apply relaxation
        results = self.relaxation_controller.relax_constraints(level, context)
        self.relaxation_results.extend(results)
        
        # Log results
        logger.info(f"Applied constraint relaxation level {level.name}")
        logger.info(f"Relaxed {len(results)} constraints")
        
        return results
        
    def get_relaxation_status(self) -> Dict[str, Any]:
        """Get current relaxation status."""
        if not self.enable_relaxation or not self.relaxation_controller:
            return {"status": "disabled"}
            
        return {
            "current_level": self.current_relaxation_level.name,
            "relaxation_enabled": self.enable_relaxation,
            "details": self.relaxation_controller.get_relaxation_status()
        }
    
    def solve(self, request: ScheduleRequest = None, 
              time_limit_seconds: int = None, 
              tune_weights: bool = False,
              with_relaxation: bool = False) -> ScheduleResponse:
        """
        Solve the scheduling problem.
        
        Args:
            request: Schedule request to solve (uses self.request if None)
            time_limit_seconds: Time limit for solver
            tune_weights: Whether to tune weights before solving
            with_relaxation: Whether to attempt constraint relaxation if
                            a solution is not found
            
        Returns:
            Schedule response with assignments
        """
        # Use provided request or stored request
        req = request if request is not None else self.request
        if not req:
            raise ValueError("Schedule request is required")
            
        # Import config at method level
        from . import config as config_module
        
        # Set time limit
        time_limit = time_limit_seconds if time_limit_seconds is not None else config_module.SOLVER_TIME_LIMIT_SECONDS
        
        # Store request for future use
        self.request = req
        
        # Tune weights if requested
        if tune_weights and config_module.ENABLE_WEIGHT_TUNING:
            self.tune_weights(req)
            
        # Create schedule
        try:
            response = self.create_schedule(req, time_limit)
            logger.info(f"Schedule created successfully with {len(response.assignments) if hasattr(response, 'assignments') else 0} assignments")
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            logger.error(f"Request details: Classes={len(req.classes)}, Date range={req.startDate} to {req.endDate}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # If no solution found and relaxation is enabled, try with relaxation
        if with_relaxation and self.enable_relaxation and (
            not response.assignments or len(response.assignments) == 0
        ):
            logger.info("No solution found, attempting with constraint relaxation")
            
            # Try with progressively increasing relaxation levels
            for level in [
                RelaxationLevel.MINIMAL,
                RelaxationLevel.MODERATE,
                RelaxationLevel.SIGNIFICANT,
                RelaxationLevel.MAXIMUM
            ]:
                logger.info(f"Trying relaxation level: {level.name}")
                self.relax_constraints(level)
                
                # Try to create schedule with relaxed constraints
                response = self.create_schedule(req, time_limit)
                
                # If we found a solution, include relaxation info and return
                if response.assignments and len(response.assignments) > 0:
                    # Add relaxation info to metadata
                    if hasattr(response, 'metadata') and response.metadata:
                        response.metadata.relaxation_level = level.name
                        response.metadata.relaxation_status = self.get_relaxation_status()
                    
                    logger.info(
                        f"Found solution with relaxation level {level.name}, "
                        f"assignments: {len(response.assignments)}"
                    )
                    return response
            
            # If still no solution, log and return the empty response
            logger.warning("Could not find solution even with maximum relaxation")
        
        return response
    
    def create_schedule(self, request: ScheduleRequest, time_limit_seconds: int = None) -> ScheduleResponse:
        """Create a schedule using the unified solver configuration"""
        # Import config at method level
        from . import config as config_module
        
        logger.info(f"Starting unified solver for {len(request.classes)} classes...")
        logger.info("\nSolver configuration:")
        logger.info("Feature flags:")
        logger.info(f"- Metrics enabled: {config_module.ENABLE_METRICS}")
        logger.info(f"- Solution comparison enabled: {config_module.ENABLE_SOLUTION_COMPARISON}")
        logger.info(f"- Experimental distribution enabled: {config_module.ENABLE_EXPERIMENTAL_DISTRIBUTION}")
        logger.info(f"- Genetic optimization enabled: {config_module.ENABLE_GENETIC_OPTIMIZATION}")
        logger.info(f"- Consecutive classes control enabled: {config_module.ENABLE_CONSECUTIVE_CLASSES}")
        logger.info(f"- Teacher breaks enabled: {config_module.ENABLE_TEACHER_BREAKS}")
        logger.info(f"- Weight tuning enabled: {config_module.ENABLE_WEIGHT_TUNING}")
        logger.info(f"- Grade grouping enabled: {config_module.ENABLE_GRADE_GROUPING}")
        logger.info(f"- Constraint relaxation enabled: {self.enable_relaxation}")
        
        if config_module.ENABLE_GENETIC_OPTIMIZATION and self.use_genetic:
            logger.info("\nGenetic algorithm configuration:")
            logger.info(f"- Population size: {config_module.GENETIC_CONFIG.POPULATION_SIZE}")
            logger.info(f"- Elite size: {config_module.GENETIC_CONFIG.ELITE_SIZE}")
            logger.info(f"- Max generations: {config_module.GENETIC_CONFIG.MAX_GENERATIONS}")
            logger.info(f"- Parallel fitness evaluation: {config_module.GENETIC_CONFIG.PARALLEL_FITNESS}")
            logger.info(f"- Adaptive control enabled: {config_module.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL}")
            if config_module.GENETIC_CONFIG.USE_ADAPTIVE_CONTROL:
                logger.info(f"- Adaptation interval: {config_module.GENETIC_CONFIG.ADAPTATION_INTERVAL} generations")
                logger.info(f"- Diversity threshold: {config_module.GENETIC_CONFIG.DIVERSITY_THRESHOLD}")
                logger.info(f"- Adaptation strength: {config_module.GENETIC_CONFIG.ADAPTATION_STRENGTH}")
            logger.info(f"- Available crossover methods: {', '.join(config_module.GENETIC_CONFIG.CROSSOVER_METHODS)}")
        
        if config_module.ENABLE_WEIGHT_TUNING:
            logger.info("\nWeight tuning configuration:")
            logger.info(f"- Meta population size: {config_module.META_CONFIG.POPULATION_SIZE}")
            logger.info(f"- Meta generations: {config_module.META_CONFIG.GENERATIONS}")
            logger.info(f"- Evaluation time limit: {config_module.META_CONFIG.EVAL_TIME_LIMIT} seconds")
            logger.info(f"- Parallel evaluation: {config_module.META_CONFIG.PARALLEL_EVALUATION}")
            
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
            current_stable = None
            if config_module.ENABLE_SOLUTION_COMPARISON and self._last_stable_response:
                current_stable = self._last_stable_response
            
            time_limit = time_limit_seconds if time_limit_seconds is not None else config_module.SOLVER_TIME_LIMIT_SECONDS
            
            if config_module.ENABLE_GENETIC_OPTIMIZATION and self.use_genetic and self.genetic_optimizer:
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
            if config_module.ENABLE_METRICS:
                self._last_run_metadata = response.metadata
                
            # Store response for future comparison if enabled
            if config_module.ENABLE_SOLUTION_COMPARISON:
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
        from . import config as config_module
        if not config_module.ENABLE_SOLUTION_COMPARISON:
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
                "duration": new_response.metadata.duration_ms - stable_response.metadata.duration_ms,
                "distribution": {
                    "score_difference": new_score - stable_score,
                    "weekly_variance_difference": (
                        (new_response.metadata.distribution.weekly.variance if new_response.metadata.distribution else 0) -
                        (stable_response.metadata.distribution.weekly.variance if stable_response.metadata.distribution else 0)
                    ),
                    "average_period_spread_difference": (
                        sum(
                            new_response.metadata.distribution.daily[date].periodSpread if new_response.metadata.distribution else 0
                            for date in new_response.metadata.distribution.daily
                        ) / len(new_response.metadata.distribution.daily) -
                        sum(
                            stable_response.metadata.distribution.daily[date].periodSpread if stable_response.metadata.distribution else 0
                            for date in stable_response.metadata.distribution.daily
                        ) / len(stable_response.metadata.distribution.daily)
                        if stable_response.metadata.distribution and new_response.metadata.distribution
                        else 0
                    )
                }
            }
        }
