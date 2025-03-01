# Active Context: Gym Class Rotation Scheduler

## Current Status (February 2025)
We have completed a major code cleanup and reorganization:

### 1. Frontend Refactoring ✅
- Removed legacy BacktrackingScheduler implementation
- Simplified frontend scheduler interface to use backend API
- Updated scheduler worker to handle async operations
- Streamlined complexity analysis for solver version selection
- Maintained all existing functionality with cleaner code

### 2. Backend Optimization ✅
- Created shared solver configuration in `config.py`
- Consolidated common constraints and objectives
- Standardized priority weights across solvers
- Enhanced development solver flexibility
- Maintained solver performance and reliability

### 3. Development Workflow ✅
Using standardized configuration between solvers:
- Base constraints and objectives in shared config
- Development version extends stable with experimental features
- Clear separation between stable and experimental code
- Easy comparison between solver versions
- Standardized weight hierarchy

### 4. Current Focus
1. Solution Quality
   - Testing alternative search strategies
   - Fine-tuning objective weights
   - Improving distribution balance
   - Enhancing early scheduling

2. Development Version
   - Experimenting with solver parameters
   - Testing new search heuristics
   - Validating quality improvements
   - Documenting successful patterns

## Priority System
Now centralized in `config.py`:
1. Required periods: 10000 (highest)
2. Early scheduling: 5000 (high)
3. Preferred periods: 1000 × weight
4. Avoid periods: -500 × weight
5. Distribution: 500
6. Earlier dates: 10 (lowest)

## Development Strategy
1. Solution Quality Focus
   - Test new search strategies
   - Balance objective weights
   - Analyze solution patterns
   - Compare with stable version

2. Implementation Approach
   - Incremental improvements in dev solver
   - A/B testing of changes
   - Quality metrics tracking
   - Clear documentation

3. Testing Strategy
   - Compare solution quality metrics
   - Validate improvements
   - Track solver performance
   - Document successful patterns

## Next Steps
1. Development Solver:
   - Implement new search strategies
   - Test objective weight adjustments
   - Try different solver parameters
   - Compare solution quality

2. Quality Metrics:
   - Define quality measures
   - Track improvements
   - Compare solutions
   - Validate changes

## Key Questions
1. Which search strategies yield best results?
2. How to better balance competing objectives?
3. What metrics best measure solution quality?
4. Which solver parameters most affect quality?

## Recent Achievements
1. Code Cleanup
   - Removed redundant frontend implementation
   - Consolidated solver configurations
   - Standardized priority weights
   - Enhanced development workflow

2. Architecture Improvements
   - Clear separation of concerns
   - Shared configuration management
   - Simplified frontend integration
   - Better type safety

3. Developer Experience
   - Cleaner codebase
   - Better documentation
   - Easier experimentation
   - Improved testing setup

## Code Organization
```
scheduler-backend/
├── app/
│   ├── scheduling/
│   │   ├── constraints/      # Core constraints
│   │   ├── objectives/       # Scheduling objectives
│   │   ├── solvers/         # Solver implementations
│   │   │   ├── config.py    # Shared configuration
│   │   │   ├── stable.py    # Production solver
│   │   │   └── dev.py       # Experimental solver
│   │   └── utils/           # Shared utilities
│   └── main.py              # API endpoints
```

## Current Constraints
All constraints now use shared configuration:
1. Single assignment per class
2. No overlapping classes
3. Teacher availability
4. Required periods
5. Conflict periods
6. Daily/weekly limits
7. Minimum periods per week

## Optimization Objectives
Standardized weights from config:
1. Required periods (highest)
2. Early scheduling
3. Preferred periods
4. Distribution balance
5. Avoided periods (penalties)
6. Earlier dates (lowest)
