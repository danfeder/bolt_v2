# System Patterns: Gym Class Rotation Scheduler

## Architecture Overview

### Frontend Architecture
```mermaid
flowchart TD
    App --> Components
    App --> Store
    Store --> Scheduler
    
    subgraph Components
        Calendar
        ClassEditor
        TeacherAvailability
        ConstraintsForm
        FileUpload
        ScheduleDebugPanel
    end
    
    subgraph Store
        scheduleStore[Schedule Store]
    end
    
    subgraph Scheduler
        subgraph "CP-SAT Solvers"
            StableV2[Stable v2]
            DevVersion[Development]
        end
    end
```

## Core Design Patterns

### 1. State Management
- **Pattern**: Centralized store using Zustand
- **Implementation**: `scheduleStore.ts`
- **Purpose**: Manage application state, schedule generation, and data persistence
- **Benefits**: Simplified state updates, predictable data flow

### 2. Development Workflow
- **Pattern**: Two-Version Development
- **Implementation**: 
  - Stable Version: `solvers/stable.py`
  - Development Version: `solvers/dev.py`
- **Key Features**:
  - Solution quality experimentation
  - Search strategy testing
  - Objective weight tuning
  - Performance monitoring

### 3. Scheduling Algorithm
- **Pattern**: CP-SAT solver with optimized search
- **Implementation**: OR-Tools CP-SAT
- **Key Features**:
  - Pre-filtered variable creation
  - Search strategy optimization
  - Quality-focused objectives
  - Multi-objective balancing
  - Performance monitoring
  - Comprehensive validation

### 4. Component Architecture
- **Pattern**: Functional components with hooks
- **Structure**:
  ```
  scheduler-backend/
  ├── app/
  │   ├── scheduling/
  │   │   ├── constraints/    # Scheduling constraints
  │   │   ├── objectives/     # Optimization objectives
  │   │   ├── solvers/       # Solver implementations
  │   │   └── utils/         # Shared utilities
  │   └── models.py          # Data models
  ```

### 5. Data Models
- **Pattern**: TypeScript interfaces and Python dataclasses
- **Core Types**:
  - TimeSlot
  - WeeklySchedule
  - Class
  - TeacherAvailability
  - ScheduleAssignment
  - ScheduleConstraints
  - SchedulerContext

## Technical Decisions

### 1. Variable Creation Strategy
- **Pattern**: Pre-filtered variable creation
- **Implementation**:
  - Only create variables for valid periods
  - Filter out conflicting periods early
  - Reduce search space significantly
  - Track variable creation in debug info

### 2. Priority System
- **Pattern**: Hierarchical weights
- **Implementation**:
  1. Required periods (10000)
  2. Early scheduling (5000)
  3. Preferred periods (1000 × weight)
  4. Avoided periods (-500 × weight)
  5. Earlier dates (10 to 0)

### 3. Search Strategy
- **Pattern**: Quality-focused search
- **Implementation**:
  - Alternative search heuristics
  - Solver parameter tuning
  - Solution pattern analysis
  - Quality metrics tracking

### 4. Data Sharing
- **Pattern**: Context-based communication
- **Implementation**:
  - SchedulerContext for shared state
  - debug_info for cross-component data
  - Quality metrics tracking
  - Enhanced logging capabilities

## Performance Patterns

### 1. Search Space Optimization
- Pre-filtered variable creation
- Quality-focused search strategies
- Solution pattern analysis
- Efficient constraint application

### 2. Development Strategies
- Solution quality experiments
- A/B testing changes
- Quality metrics tracking
- Pattern documentation

## Error Handling
- Detailed variable creation logs
- Constraint validation feedback
- Quality metric monitoring
- Performance tracking metrics

## Testing Strategy
- Solution quality verification
- Search strategy validation
- Quality metrics tracking
- Performance benchmarking
