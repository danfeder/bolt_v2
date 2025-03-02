# Directory Structure Analysis

**Task ID**: A-01  
**Status**: Completed  
**Date**: March 2, 2025  

## 1. Current Directory Structure

### 1.1 Top-Level Organization

The Gym Class Rotation Scheduler project is organized into these main components:

```
bolt_v2/
├── scheduler-backend/       # Backend scheduling engine (Python/FastAPI)
│   ├── app/                 # Application code
│   ├── tests/               # Backend tests
│   └── various other dirs   # Coverage reports, venv, etc.
├── src/                     # Frontend code (React/TypeScript)
│   ├── components/          # React components
│   ├── store/               # State management
│   └── types/               # TypeScript definitions
├── memory-bank/             # Documentation files
│   └── implementationPhases/# Phase-specific documentation
├── coverage/                # Frontend test coverage reports
├── data/                    # Data files
└── various config files     # Configuration for TypeScript, Jest, etc.
```

### 1.2 Backend Structure

```
scheduler-backend/app/
├── scheduling/              # Core scheduling logic
│   ├── constraints/         # Scheduling constraints
│   ├── objectives/          # Optimization objectives
│   ├── solvers/             # Solver implementations
│   │   ├── genetic/         # Genetic algorithm implementation
│   │   │   └── experiments/ # Experimental features
│   │   └── legacy/          # Legacy solver code
│   └── utils/               # Utility functions
├── utils/                   # General utility functions
└── visualization/           # Visualization code (should be in frontend)
```

### 1.3 Frontend Structure

```
src/
├── components/              # React components
│   ├── ScheduleViewer/      # Schedule visualization
│   ├── dashboard/           # Dashboard components
│   └── solver/              # Solver configuration UI
├── __mocks__/               # Test mocks
├── __tests__/               # Frontend tests
│   └── components/          # Component tests
├── lib/                     # Utility libraries
├── store/                   # State management (Zustand)
└── types/                   # TypeScript type definitions
```

### 1.4 Documentation Structure

The `memory-bank/` directory contains numerous markdown files with project documentation:

```
memory-bank/
├── implementationPhases/    # Phase-specific documentation
│   ├── phase1_config.md
│   ├── phase2_metrics.md
│   ├── phase3_parallel.md
│   └── phase4_experiment.md
├── various markdown files   # General documentation
└── README.md                # Documentation overview
```

## 2. Issues Identified

### 2.1 Mixed Concerns

1. **Backend Visualization Logic**: 
   - The backend (`scheduler-backend/app/visualization/`) contains visualization code that should be in the frontend.
   - This creates a coupling between frontend and backend that complicates maintenance.

2. **Redundant Model Definitions**:
   - Multiple model definitions exist:
     - `scheduler-backend/app/models.py`
     - `scheduler-backend/app/visualization/models.py`
   - Frontend likely reimplements similar models in TypeScript.

### 2.2 Generated Files

1. **Coverage Reports**:
   - Multiple coverage directories:
     - `./coverage/` (Frontend)
     - `./scheduler-backend/coverage_report/` (Backend)
     - `./scheduler-backend/htmlcov/` (Backend)
   - These should be gitignored and not committed to the repository.

2. **Temporary Files**:
   - Various temporary files and directories that should be cleaned up or gitignored.

### 2.3 Documentation Scatter

1. **No Clear Structure**:
   - Documentation is spread across 25+ markdown files in `memory-bank/`.
   - No clear organization or hierarchy between files.
   - Some documentation appears redundant or outdated.

2. **Implementation Phases**:
   - Implementation phases are documented separately from the main documentation.
   - No clear linkage between phases and overall project documentation.

### 2.4 Testing Organization

1. **Inconsistent Test Structure**:
   - Frontend tests are in `src/__tests__/`
   - Backend tests are in `scheduler-backend/tests/`
   - No consistent pattern for test organization.

## 3. Recommendations

### 3.1 Directory Reorganization

```
bolt_v2/
├── scheduler-backend/           # Backend scheduling engine
│   ├── app/                     # Application code
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Core scheduling logic
│   │   │   ├── constraints/     # Scheduling constraints
│   │   │   ├── objectives/      # Optimization objectives
│   │   │   └── solvers/         # Solver implementations
│   │   └── models/              # Data models
│   ├── tests/                   # Backend tests
│   │   ├── unit/                # Unit tests
│   │   ├── integration/         # Integration tests
│   │   └── performance/         # Performance tests
│   └── docs/                    # Backend-specific documentation
├── scheduler-frontend/          # Frontend visualization
│   ├── src/                     # Source code
│   │   ├── components/          # React components
│   │   ├── store/               # State management
│   │   └── api/                 # API client
│   ├── tests/                   # Frontend tests
│   │   ├── unit/                # Unit tests
│   │   └── integration/         # Integration tests
│   └── docs/                    # Frontend-specific documentation
├── docs/                        # Consolidated documentation
│   ├── architecture/            # System architecture
│   ├── requirements/            # Project requirements
│   └── roadmap/                 # Project roadmap
└── tools/                       # Development tools
    └── scripts/                 # Build and deployment scripts
```

### 3.2 Cleanup Actions

1. **Move Visualization Logic**: 
   - Move all visualization code from the backend to the frontend.
   - Create a clear API boundary between frontend and backend.

2. **Consolidate Models**: 
   - Define a single source of truth for data models.
   - Generate TypeScript interfaces from backend models if possible.

3. **Clean up Generated Files**:
   - Update `.gitignore` to exclude all coverage reports.
   - Create a dedicated directory for all generated files.

4. **Reorganize Documentation**:
   - Implement a documentation system using MkDocs or Sphinx.
   - Create a clear hierarchy and organization for documentation.

### 3.3 Specific Files to Address

1. **Coverage Reports**:
   - All files in `./coverage/`, `./scheduler-backend/coverage_report/`, and `./scheduler-backend/htmlcov/` should be removed from version control.

2. **Visualization Models**:
   - `scheduler-backend/app/visualization/models.py` should be moved to frontend.

3. **Redundant Documentation**:
   - Consolidate redundant documentation files in `memory-bank/`.

## 4. Implementation Plan

### 4.1 Short-term Actions

1. Update `.gitignore` to exclude coverage reports.
2. Create directory for consolidated documentation.
3. Establish clear model boundaries between frontend and backend.

### 4.2 Medium-term Actions

1. Move visualization logic from backend to frontend.
2. Reorganize directory structure according to recommendations.
3. Implement documentation system.

### 4.3 Long-term Actions

1. Refactor code to align with new directory structure.
2. Complete migration of all documentation to new system.
3. Establish documentation maintenance process.

## 5. Conclusion

The current directory structure of the Gym Class Rotation Scheduler project has several issues related to mixed concerns, redundancy, and organization. By implementing the recommended directory reorganization and cleanup actions, we can create a more maintainable, modular, and comprehensible codebase that aligns with best practices for full-stack application development.
