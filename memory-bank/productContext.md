# Product Context: Gym Class Rotation Scheduler

## Current Development Phase
We are implementing the scheduler in a phased approach, focusing on one set of constraints at a time to ensure robustness and maintainability.

### Current Implementation (Phase 1 Complete)
- Basic scheduling engine using CP-SAT solver
- Core constraints: weekdays, valid periods, no overlaps
- Conflict period avoidance
- Basic schedule optimization

### Target Implementation (Phase 2 In Progress)
- Required periods assignment
- Teacher unavailability handling
- Comprehensive validation
- Detailed error reporting

## Core Functionality
The scheduler must handle:
1. Time Slot Validation
   - Weekday scheduling only
   - Valid periods (1-8)
   - No overlapping classes
   - Respect conflicts and requirements

2. Assignment Rules
   - Single assignment per class
   - Maximum classes per day/week
   - Minimum periods per week
   - Consecutive class rules

3. Teacher Availability
   - Unavailable period blocking
   - Teaching load limits

4. Period Preferences
   - Required periods (hard constraint)
   - Preferred periods (soft constraint)
   - Avoid periods (soft constraint)

5. Schedule Optimization
   - Minimize total duration
   - Even distribution
   - Preference satisfaction

## Testing Strategy
Each phase includes:
1. Unit tests for new constraints
2. Integration tests for constraint combinations
3. Performance testing with various dataset sizes
4. Validation and error reporting

## Success Metrics
- All hard constraints satisfied
- Soft constraints optimized where possible
- Clear error reporting
- Performance within acceptable limits
- Comprehensive test coverage
