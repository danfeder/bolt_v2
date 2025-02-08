# Scheduling Algorithm Requirements

## Hard Constraints
1. Time Slot Validity
   - Classes only on weekdays
   - Valid periods (1-8)
   - No scheduling during conflicts
   - Respect teacher unavailability
   - Required periods must be assigned

2. Assignment Rules
   - Each class scheduled exactly once
   - Maximum classes per day limit
   - Maximum classes per week limit
   - Minimum periods per week
   - Consecutive classes limit (when set as hard constraint)

3. Teacher Availability
   - No scheduling during teacher unavailable slots
   - Daily/weekly teaching load limits

## Soft Constraints
1. Period Preferences
   - Preferred periods
   - Avoid periods

2. Scheduling Preferences
   - Consecutive classes (when set as soft constraint)

## Optimization Objectives
1. Primary Goals
   - Satisfy all required period assignments (mandatory)
   - Maximize preferred period assignments
   - Minimize avoided period assignments

2. Secondary Goals
   - Minimize total schedule duration from start date
   - Balanced distribution within minimal duration:
     * Even distribution of classes across active weeks (within min/max bounds)
     * Even distribution of classes within each active week
   - Minimize consecutive classes (soft constraint)

## Performance Considerations
1. Caching Strategies
   - Valid time slot caching
   - Daily assignment count tracking
   - Weekly assignment count tracking
   - Date string caching

2. Optimization Techniques
   - Class ordering by constraint complexity
   - Randomized slot selection for better solutions
   - Progress tracking
   - Early constraint validation

## Validation Requirements
1. Schedule Verification
   - Daily limits check
   - Weekly limits check
   - Consecutive classes check
   - Complete schedule check
   - Single assignment per class

2. Error Handling
   - Clear error messages
   - Specific constraint violation feedback
   - Suggested resolution steps
