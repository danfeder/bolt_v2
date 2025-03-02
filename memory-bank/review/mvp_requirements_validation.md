# MVP Requirements Validation

## Overview
This document validates and clarifies the Minimum Viable Product (MVP) requirements for the Gym Class Rotation Scheduler. It extracts requirements from existing documentation, categorizes them as MVP or post-MVP, identifies ambiguous requirements, and documents validation criteria.

## 1. Core MVP Requirements

### 1.1 Schedule Generation Engine

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Classes scheduled on weekdays only | MVP | Clear | Schedule contains assignments only on Mon-Fri |
| Valid periods (1-8) | MVP | Clear | All assignments are within periods 1-8 |
| No overlapping classes | MVP | Clear | No two classes scheduled in same day/period |
| Single assignment per class | MVP | Clear | Each class appears exactly once in schedule |
| Respect conflict periods | MVP | Clear | No class scheduled during its conflict periods |
| Maximum classes per day limit | MVP | Clear | No day exceeds configured max classes limit |
| Maximum classes per week limit | MVP | Clear | No week exceeds configured max classes limit |
| Minimum periods per week | MVP | Ambiguous | Unclear if this applies to each class or overall schedule |
| Consecutive classes limit | MVP | Clear | No more than configured consecutive classes |

### 1.2 Data Management

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Import class data from CSV | MVP | Clear | Successfully parse valid CSV file |
| Import teacher availability | MVP | Clear | Successfully parse availability data |
| Edit class information | MVP | Clear | UI allows editing of class details |
| Configure scheduling constraints | MVP | Clear | UI provides constraint configuration |

### 1.3 User Interface

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Interactive calendar view | MVP | Clear | Displays schedule in calendar format |
| Setup tab for data import | MVP | Clear | Tab exists with import functionality |
| Visualize tab for schedule view | MVP | Clear | Tab exists with schedule visualization |
| Dashboard tab for analytics | MVP | Clear | Tab exists with basic analytics |
| Debug tab for solver details | MVP | Clear | Tab exists with solver information |

### 1.4 API and Backend Services

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Schedule generation endpoint | MVP | Clear | `/schedule/stable` endpoint works |
| Schedule comparison endpoint | MVP | Clear | Endpoint exists for comparing schedules |
| Dashboard data endpoint | MVP | Clear | Endpoint returns dashboard metrics |
| Error handling and reporting | MVP | Clear | APIs return structured error responses |

## 2. Post-MVP Requirements

### 2.1 Advanced Scheduling Features

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Required periods assignment | Post-MVP | Clear | Classes assigned to specific required periods |
| Teacher unavailability handling | Post-MVP | Clear | No assignments during teacher unavailable periods |
| Preferred periods (soft constraint) | Post-MVP | Clear | Schedule prefers these periods when possible |
| Genetic algorithm optimization | Post-MVP | Clear | GA produces better schedules than basic solver |
| Schedule quality visualization | Post-MVP | Clear | Visualizations show quality metrics |

### 2.2 Advanced UI Features

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Schedule export (PDF, CSV, iCal) | Post-MVP | Clear | Export functionality works for each format |
| Drag-and-drop class editing | Post-MVP | Clear | UI supports drag-drop for schedule modification |
| Advanced filtering options | Post-MVP | Clear | UI includes filtering by grade, class, etc. |
| Light/dark mode support | Post-MVP | Clear | UI supports theme switching |
| Schedule comparison view | Post-MVP | Clear | Side-by-side comparison of schedules |

### 2.3 Advanced Analytics

| Requirement | MVP Status | Ambiguity | Validation Criteria |
|-------------|------------|-----------|---------------------|
| Schedule quality metrics | Post-MVP | Clear | Dashboard shows comprehensive metrics |
| Grade-period distribution heatmap | Post-MVP | Clear | Heatmap visualization available |
| Constraint satisfaction breakdown | Post-MVP | Clear | Detailed constraint satisfaction analysis |
| Schedule history comparison | Post-MVP | Clear | Compare metrics across schedule versions |

## 3. Ambiguous Requirements Analysis

### 3.1 "Minimum periods per week"
- **Description**: The requirement to have a minimum number of periods scheduled per week
- **Ambiguity**: It's unclear whether this applies:
  - To each individual class (e.g., each class must be scheduled at least X times per week)
  - Or to the overall schedule (e.g., at least X periods must have classes scheduled)
- **Recommended Clarification**: Define this as a global constraint that requires a minimum number of total assignments across all classes per week

### 3.2 "Balanced distribution within minimal duration"
- **Description**: Classes should be evenly distributed across the schedule
- **Ambiguity**: The definition of "balanced" is subjective and could be interpreted multiple ways:
  - Even distribution across days?
  - Even distribution across periods?
  - Equal number of classes per day?
- **Recommended Clarification**: Define specific metrics for balance (e.g., standard deviation of class count per day should be ≤ 1.5)

### 3.3 "Consecutive classes (when set as soft constraint)"
- **Description**: The handling of consecutive classes as a soft constraint
- **Ambiguity**: It's unclear how the soft constraint version differs from the hard constraint:
  - Is it a penalty per consecutive class?
  - Is there a threshold before penalties apply?
- **Recommended Clarification**: Define a penalty value for each consecutive class instance that exceeds the preferred limit

## 4. Validation Criteria for MVP Features

### 4.1 Schedule Generation

- **Valid Schedule**: 
  - All classes assigned exactly once
  - No conflicts with specified conflict periods
  - No overlapping assignments
  - All assignments on weekdays in periods 1-8
  - Daily and weekly class limits respected
  - Consecutive class limits respected

- **Minimal Duration**:
  - Schedule uses earliest available dates possible
  - No unnecessary gaps between scheduled days

- **Algorithm Performance**:
  - Generates schedule for 33 classes within 30 seconds
  - Successfully handles test dataset (Schedule_From_Json_Corrected.csv)

### 4.2 User Interface

- **Data Import**:
  - Successfully parses valid CSV files
  - Reports clear errors for invalid files
  - Allows editing imported data

- **Schedule Visualization**:
  - Displays complete schedule in calendar view
  - Shows class details on hover/click
  - Correctly represents all assignments

- **Configuration**:
  - Allows setting all required constraints
  - Validates input values
  - Persists configuration between sessions

### 4.3 API Services

- **Schedule Endpoint**:
  - Returns valid response with assignments
  - Includes metadata about generation process
  - Provides clear error messages for invalid requests

- **Error Handling**:
  - Structured error format
  - Meaningful error messages
  - Appropriate HTTP status codes

## 5. Current Implementation Status

### 5.1 Implemented MVP Features

- ✅ Basic scheduling engine using CP-SAT solver
- ✅ Core constraints (weekdays, valid periods, no overlaps)
- ✅ Conflict period avoidance
- ✅ Basic schedule optimization
- ✅ CSV data import
- ✅ Calendar visualization
- ✅ TabContainer navigation system
- ✅ Configuration interface
- ✅ Schedule generation API

### 5.2 In-Progress MVP Features

- 🔄 Dashboard view implementation
- 🔄 Error handling improvements
- 🔄 Test coverage expansion

### 5.3 Pending MVP Features

- ❌ Comprehensive validation feedback
- ❌ Some constraint configuration options

## 6. Recommendations

### 6.1 Priority Clarifications Needed

1. **Minimum periods per week**: Clearly define scope (per class or global)
2. **Balanced distribution**: Define specific metrics for "balanced"
3. **Soft constraints**: Clarify penalty mechanisms for soft constraint violations

### 6.2 Documentation Improvements

1. Create a unified requirements specification document
2. Document validation criteria for each requirement
3. Create user stories for key MVP features

### 6.3 Testing Recommendations

1. Create specific test cases for each validation criterion
2. Develop automated tests for all MVP requirements
3. Implement consistent validation reporting

## 7. Conclusion

The Gym Class Rotation Scheduler project has a well-defined set of MVP requirements, with most core scheduling features clearly articulated. Most ambiguities are in the optimization objectives rather than the core functionality. The current implementation has successfully delivered many of the MVP requirements, with a few remaining features in progress.

By addressing the identified ambiguities and completing the in-progress features, the project can achieve a robust MVP that satisfies the core scheduling needs while establishing a foundation for the more advanced post-MVP features.
