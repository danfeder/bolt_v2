# Suggestions to Simplify and Streamline the Gym Class Rotation Scheduler

Below are some concrete suggestions to simplify or streamline the project while preserving (and potentially even enhancing) the existing functionality. These recommendations address both **architecture** (how the code is structured) and **development workflow** (how you add or modify features) so that your scheduler remains maintainable and clear.

---

## 1. Centralize Core Logic and Eliminate Duplication

### 1.1 Consolidate Stable & Development Solvers
Right now, there are two solver files—`stable.py` and `dev.py`—that share common logic (constraints, objective definitions, scheduling process). Instead of having two almost-parallel solvers, consider:

- **Use a Single Solver File** with toggles or "feature flags" for experimental settings.  
- Keep any truly experimental code (new heuristics, alternative search loops) in a well-labeled, optional function or parameter that can be activated from a configuration value.

**Why This Helps**  
It ensures there is exactly one location for your solver flow—building the model, applying constraints, and defining objectives. You avoid duplicating logic and diverging code paths, which gets messy over time.

### 1.2 Merge Overlapping Constraints
If certain constraints appear both in `constraints/` files and in your "dev vs. stable" solver code, unify them. Constraints can be classes with toggles. For example:

    # Example pseudo-code
    constraint = SomeConstraint(
      enabled=context.dev_mode,      # or a param from config
      penalty_weight=500
    )

Doing this removes the need for a "dev constraints folder" vs. a "stable constraints folder." You simply pass different parameters to the same constraint classes.

---

## 2. Simplify Configuration Management

### 2.1 Single Source of Truth
You have a robust set of weight definitions (e.g., required periods = 10,000, etc.) scattered across multiple files. Move them into **one** configuration module (for instance, `solvers/config.py`). Then, load this config from environment variables or a JSON file if you need different environments or "profiles."

### 2.2 Configuration as Data, Not Code
Rather than hard-coding weight constants throughout the code, define them in a structured data format:

    SCHEDULER_CONFIG = {
      "required_period_weight": 10000,
      "early_scheduling_weight": 5000,
      "preferred_period_weight": 1000,
      # ...
    }

Then reference `SCHEDULER_CONFIG["required_period_weight"]` anywhere needed. This keeps all weights in one place, easy to tweak and maintain.

---

## 3. Introduce a Layered Architecture for Constraints & Objectives

Right now, each constraint is a standalone class. That's good, but you could go even further in standardizing how constraints are applied:

1. **Core "ConstraintManager"**: A single orchestrator that:
   - Enumerates all constraints you want active.
   - Applies them in a known order to the CP-SAT model.

2. **Constraint Classes**:  
   - Each constraint class implements a standard interface, for example:

         class BaseConstraint:
             def apply(self, context: SchedulerContext) -> None:
                 pass

   - Possibly give each constraint an optional "priority" or "enabled" flag.

3. **ObjectiveManager**: Similarly, unify how your objectives are added. A single place, e.g.:

         class ObjectiveManager:
             def apply_objectives(self, context: SchedulerContext) -> None:
                 # Weighted sum or multi-objective approach

With these managers, your main solver code might simply be:

    model = cp_model.CpModel()
    constraint_manager.apply_all(context)   # apply constraints in consistent order
    objective_manager.apply(context)        # define objective
    solution = solver.Solve(model)

This ensures your solver code remains short, and all constraint specifics reside in well-organized classes.

---

## 4. Reduce Frontend Complexity by Embracing a Single Flow

Currently, the frontend has multiple components (Calendar, ClassEditor, ConstraintsForm, etc.) plus a debug panel. If it feels complicated, consider:

1. **One "Master" Scheduling Page** that displays a step-by-step workflow:
   - **Step 1**: Upload data (CSV).
   - **Step 2**: Edit constraints.
   - **Step 3**: Run the solver & see the results.
   - **Step 4**: Debug or tweak advanced settings (only if needed).

2. **React Router or Tabbed UI** to separate concerns:
   - A simple Tab #1 "Setup," Tab #2 "Visualize," Tab #3 "Debug."
   - Each tab only loads relevant components.

3. **Leverage a Single State Manager** (which you already have with Zustand) so you do not need to pass props all over the place.

---

## 5. Use a Modular Testing Strategy

### 5.1 Test Constraints in Isolation
Each constraint class should have at least one small unit test verifying it indeed enforces (or forbids) the correct things. This keeps changes small.

### 5.2 Test the Whole Scheduler with a Known Dataset
You already mention testing with `Schedule_From_Json_Corrected.csv`. This is perfect for an end-to-end test. Continue to keep this test script as minimal as possible—just load the CSV, apply constraints, run the solver, and check final constraints are satisfied.

### 5.3 Factor Out Repetitive Integration Logic
If your "test_scheduler.py" does the same setup code for multiple tests, you can factor that out into a small helper function or fixture. This keeps each test concise.

---

## 6. Provide Clear Documentation & Onboarding

A key step in simplifying the perceived complexity is making sure a new contributor (or your future self) can quickly understand the flow. You can do this by:

1. **Single README Explaining the End-to-End Flow**  
   - Where the user sets constraints.  
   - How they run the solver.  
   - Where logs or debug info appear.

2. **Short Docs in the Code**  
   - Each constraint or objective class has a docstring explaining what it does and how it interacts with the solver.  
   - The solver "main flow" file is heavily commented in plain English: "1) load data, 2) apply constraints, 3) define objective, 4) solve, 5) return result."

3. **Deprecate or Remove Obsolete Files**  
   - If any older system is not used (like a "BacktrackingScheduler" leftover or partially integrated code), remove or archive it in a separate branch.

---

## 7. Consider a Serverless or Microservice Approach Only If Needed

You have a plan for "Serverless Integration" and parallel workers. This is valuable for scalability, but it can add complexity:

- If local (single-machine) CP-SAT solves in a few seconds for your typical dataset, a complex serverless approach might not be necessary.
- Or, you can unify a "local vs. serverless" approach behind a single interface so that everything else in your system doesn't care which solver it calls.

Keep an eye on whether your project truly needs this distribution or if it's an optimization best left for advanced cases. A single-process solve might remain simpler and good enough.

---

## Summary of Key Recommendations

1. ✅ **Merge stable & dev solvers** into one solver code path, toggling features by config or environment variables.  
2. ✅ **Centralize constraint logic** with a "ConstraintManager" (and an analogous "ObjectiveManager") to reduce repeated code.  
3. ✅ **Keep a single configuration file** for all weight definitions and solver toggles.  
4. ✅ **Simplify the frontend** with a guided, tab-based workflow using a single global store (Zustand).  
5. ✅ **Clean up tests** to keep them either very small (for each constraint) or truly end-to-end (for the entire scheduling run).  
6. ⬜ **Improve documentation** with one main README describing how the code is structured, how to add constraints, and how the solver is run.  
7. ✅ **Remove or archive legacy code** that duplicates functionality or is no longer needed.

---

## Implementation Roadmap (Actionable Checklist)

### Phase 1 - Backend Refactor (Weeks 1-3)
- [x] **Solver Consolidation**
  - [x] Create unified `solver.py` by merging logic from `stable.py` and `dev.py`
  - [x] Implement feature flag system in `scheduler-backend/app/scheduling/solvers/config.py`:
    ```python
    from dataclasses import dataclass, field
    import os

    @dataclass
    class SolverConfig:
        ENABLE_EXPERIMENTAL_SEARCH: bool = False
        USE_PARALLEL_CONSTRAINTS: bool = True
        WEIGHTS: dict = field(default_factory=lambda: {
            'required_period': 10000,
            'preferred_period': 1000,
            'instructor_conflict': 5000
        })

        @classmethod
        def from_env(cls):
            return cls(
                ENABLE_EXPERIMENTAL_SEARCH=os.getenv('ENABLE_EXPERIMENTAL', '0') == '1',
                USE_PARALLEL_CONSTRAINTS=os.getenv('PARALLEL_CONSTRAINTS', '1') == '1'
            )
    ```
  - [x] Archive legacy solver files (`stable.py` and `dev.py`) into a `legacy/` folder or branch.

- [x] **Constraint System**
  - [x] Create a `BaseConstraint` abstract class in `scheduler-backend/app/scheduling/constraints/base.py`
  - [x] Develop `ConstraintManager` to load and apply constraints in a consistent order.
  - [x] Refactor existing constraints to inherit from `BaseConstraint` and remove redundant code.
  - [x] Add comprehensive test harness for constraint testing
  - [x] Fix base constraint inheritance issues for all constraint types
  - [x] Add improved validation to constraint tests with debugging output

### Phase 2 - Frontend Simplification (Week 4)
- [x] **Tabbed Interface Implementation**
  - [x] Create tab state management in `src/store/scheduleStore.ts`
  - [x] Implement a guided workflow component (Wizard/Setup flow) via TabContainer
  - [x] Migrate existing components to a tab-based structure
  
- [x] **Genetic Algorithm Frontend Integration**
  - [x] **Extend Solver Configuration Panel:**
    - Update the existing SolverConfig component (e.g., in `src/components/SolverConfig.tsx`) to include a toggle for "Genetic Optimization" that corresponds to the backend flag (`ENABLE_GENETIC_OPTIMIZATION`).
    - When enabled, reveal additional controls for configuring genetic parameters (e.g., population size, mutation rate, crossover rate, max generations). These values should be managed via the global state (using Zustand) to be included in the scheduling request.
  - [x] **Update Scheduling Request Flow:**
    - Modify the scheduling request payload to include the genetic optimization option and parameters.
    - Display an indicator on the scheduling results page (or within the Schedule Comparison component) showing when the genetic solver was used.
  - [x] **Debug & Metrics Panel Enhancements:**
    - Enhance the existing Schedule Debug Panel to display genetic-specific metrics (e.g., generation count, best fitness, population diversity).
    - Ensure these metrics integrate with the current solution comparison and metrics tracking.

### Phase 3 - Testing & Validation (Week 5)
- [x] **Modular Testing Strategy**
  - [x] Develop a test harness for isolated constraint testing
  - [x] Create unit tests for each constraint class
  - [x] Fix test harness forcing logic for constraint violations
  - [x] Add detailed debug output to test harness
  - [x] Verify all constraint tests with final coverage over 90%
  - [ ] Set up integration testing using Schedule_From_Json_Corrected.csv to validate end-to-end functionality

### Phase 4 - Documentation (Ongoing)
- [ ] **Architecture & Onboarding**
  - [ ] Update the main README with an overview of the new architecture, including diagrams
  - [ ] Create a `CONSTRAINT_ADD_GUIDE.md` detailing how to add and test new constraints
  - [ ] Add test harness usage documentation
  - [ ] Add constraint validation guide

### Phase 5 - Alternative Solver Implementation
- [x] **Genetic Algorithm Integration**
  - [x] Create modular genetic algorithm components:
    ```python
    scheduler-backend/app/scheduling/solvers/
    └── genetic/
        ├── chromosome.py    # Schedule representation
        ├── population.py    # Evolution management
        ├── fitness.py       # Solution evaluation
        └── optimizer.py     # Main optimization logic
    ```
  - [x] Implement feature toggle in unified solver:
    ```python
    ENABLE_GENETIC_OPTIMIZATION = bool(int(os.getenv('ENABLE_GENETIC_OPTIMIZATION', '0')))
    ```
  - [x] Add genetic algorithm configuration:
    ```python
    @dataclass
    class GeneticConfig:
        POPULATION_SIZE: int = 100
        ELITE_SIZE: int = 2
        MUTATION_RATE: float = 0.1
        CROSSOVER_RATE: float = 0.8
        MAX_GENERATIONS: int = 100
    ```
  - [x] Integrate with unified solver through feature flag
  - [x] Add comprehensive unit tests for genetic components
  - [x] Maintain compatibility with existing constraint system

The genetic algorithm solver provides an alternative optimization approach that can be enabled through configuration. It maintains all the benefits of our unified architecture while offering:
- Natural handling of competing objectives through fitness-based evolution
- Potential for better solutions in complex, non-linear scenarios
- Easy experimentation through configurable genetic parameters

This implementation follows our architectural principles:
- Uses the same constraint validation system
- Configurable through environment variables
- Integrates seamlessly with metrics and solution comparison
- Fully tested with both unit and integration tests

### Additional Validation Steps
- [x] Ensure backend test coverage is above 90% for constraint system
- [x] Validate that constraint loading order and application logic remain consistent
- [ ] Conduct a full integration test using Schedule_From_Json_Corrected.csv
