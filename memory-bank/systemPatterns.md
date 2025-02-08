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
            StableV1[Stable v1]
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
  - Stable Version: `or-tools-cp.ts`
  - Development Version: `or-tools-cp-dev.ts`
- **Key Features**:
  - Clear separation of concerns
  - Safe feature development
  - Easy comparison testing
  - Reliable fallback option

### 3. Scheduling Algorithm
- **Pattern**: CP-SAT solver with hierarchical constraints
- **Implementation**: OR-Tools CP-SAT
- **Key Features**:
  - Required periods enforcement
  - Teacher availability handling
  - Efficient constraint satisfaction
  - Multi-objective optimization
  - Performance monitoring
  - Comprehensive validation

### 4. Component Architecture
- **Pattern**: Functional components with hooks
- **Structure**:
  ```
  src/
  ├── components/    # UI components
  ├── lib/          # Core business logic
  ├── store/        # State management
  └── types/        # TypeScript definitions
  ```

### 5. Data Models
- **Pattern**: TypeScript interfaces for type safety
- **Core Types**:
  - TimeSlot
  - WeeklySchedule (with required periods)
  - Class
  - TeacherAvailability (with timezone handling)
  - ScheduleAssignment
  - ScheduleConstraints
  - RequiredPeriod
  - UnavailableSlot

## Technical Decisions

### 1. Framework Selection
- **React**: Component-based UI development
- **TypeScript**: Type safety and developer experience
- **Vite**: Fast development and build tooling
- **Tailwind**: Utility-first styling

### 2. State Management
- **Choice**: Zustand over Redux/MobX
- **Rationale**: 
  - Simpler API
  - Built-in TypeScript support
  - Minimal boilerplate
  - Good performance

### 3. Scheduling Implementation
- **Approach**: CP-SAT solver with hierarchical constraints
- **Benefits**:
  - Required periods prioritization
  - Teacher availability respect
  - Efficient constraint solving
  - Safe feature development
  - Easy testing and validation
  - Performance optimization
- **Workflow**:
  - Stable version with all features
  - Development version for new features
  - Thorough testing before promotion
  - Clear validation criteria
- **Constraint Hierarchy**:
  1. Required periods (highest priority)
  2. Teacher availability
  3. Basic scheduling rules
  4. Optimization preferences

### 4. Data Validation
- **Strategy**: Multi-level validation
  - Type checking with TypeScript
  - Required periods validation
  - Teacher availability verification
  - Runtime constraint validation
  - Schedule verification
  - User input validation
  - Timezone consistency checks

## Performance Patterns

### 1. Optimization
- Required periods prioritization
- Teacher availability tracking
- Valid time slot caching
- Daily/weekly assignment count tracking
- Date string memoization
- Timezone-aware date handling

### 2. Development Strategies
- Feature isolation in development version
- Comprehensive testing before promotion
- Performance comparison with stable version
- Clear validation requirements

## Error Handling
- Comprehensive error messages
- User-friendly error display
- Detailed validation feedback
- Debug panel for troubleshooting
