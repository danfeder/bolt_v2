# Testing Plan: Full Dataset Approach

This testing plan uses the full dataset provided in `data/Schedule_From_Json_Corrected.csv` for all test cases. The goal is to validate our scheduler's functionality by applying every constraint on the actual data, rather than using artificially small datasets.

## Overview
- **Data Source:** `data/Schedule_From_Json_Corrected.csv`
- **Number of Classes:** 33 (as loaded from the CSV)
- **Key Constraints to Validate:**
  - **Time Slot Validity:** 
    - Classes are only scheduled on weekdays (Mon-Fri) and in valid periods (1-8).
  - **Conflict Period Avoidance:** 
    - No class is scheduled during any conflict period provided in the CSV.
  - **Assignment Rules:** 
    - Each class is scheduled exactly once.
    - No overlapping classes occur in the same day/period.
  - **Optimization Objective:** 
    - The schedule minimizes the total duration by preferring early dates and lower periods.
  - **(Upcoming in Phase 2) Required Periods & Teacher Unavailability:**
    - While these are not yet implemented, the plan is to extend tests later using the full dataset.

## Testing Steps

### 1. Schedule Generation
- Run the complete scheduler (phase 1 implementation) with the full CSV dataset.
- Verify that:
  - The CSV is correctly parsed and all 33 classes are loaded.
  - The scheduler generates a schedule with exactly 33 assignments.
  - The server logs print detailed conflict constraints, objective details, and a schedule summary.

### 2. Validation of Hard Constraints
- **Time Slot Validity:**
  - Confirm that all assignments are on weekdays and within period 1-8.
- **Assignment Rules:**
  - Verify each class is assigned exactly once.
  - Check the schedule summary to ensure there are no overlapping assignments within the same day/period.
- **Conflict Periods:**
  - Validate using the detailed “Class Conflicts Summary” output that none of the assignments falls on a conflict period specified for their class.
  
### 3. Inspection of Optimization Objective
- Examine the generated schedule and the computed score.
  - The objective should favor earlier dates and lower periods.
  - The solver logs should indicate that the objective function was added.
  
### 4. Full Schedule Analysis
- Use the Debug Panel’s “Download Schedule Data” functionality to export the complete schedule.
- Manually (or with automated scripts) compare:
  - Each class’s scheduled time slot against its conflict list.
  - The distribution of classes across days.
  
### 5. Automated Script Option (Optional)
- Develop a simple script to:
  - Load the full CSV using the existing CSV parser.
  - Run the scheduler automatically.
  - Compare each assignment with the corresponding class’s conflict periods.
  - Report any violations or anomalies.
  
## Expected Results
- **Conflict Constraints:** All conflict constraints (as per CSV) are respected, with logging output confirming the number of conflict constraints added (e.g., "Added 888 conflict constraints").
- **Assignment Completeness:** The schedule has 33 assignments with no double-booking and without any assignment falling into a conflict period.
- **Distribution:** Classes are spread over the earliest available dates (as per the optimization objective), favoring early periods.
- **Performance:** The scheduler completes within reasonable time, and the full dataset is handled without memory/performance issues.

## Success Criteria
- All hard constraints (time slot validity, single assignment, conflict avoidance) pass validation.
- The objective function is effective in placing assignments early.
- Detailed validation output (printed in the terminal) confirms that no violations occur.
- The full dataset is used for testing, ensuring real-world conditions.

---

This plan ensures that our tests are comprehensive by using the entire dataset, giving us confidence that our scheduler behaves correctly under real conditions.
