# Directory Reorganization Plan

**Task ID**: P-01  
**Status**: Completed  
**Date**: March 2, 2025  
**Dependencies**: A-01 (Directory Structure Analysis)

## 1. Introduction

This document presents a comprehensive plan for reorganizing the Gym Class Rotation Scheduler project's directory structure. Based on the findings from the Directory Structure Analysis (Task A-01), this plan provides a detailed approach for implementation, including the proposed structure, migration strategy, and risk mitigation.

## 2. Proposed Directory Structure

### 2.1 Top-Level Organization

```
bolt_v2/
├── scheduler-backend/           # Backend scheduling engine
│   ├── app/                     # Application code
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Core scheduling logic
│   │   ├── models/              # Data models
│   │   └── utils/               # Utility functions
│   ├── tests/                   # Backend tests
│   ├── docs/                    # Backend-specific documentation
│   └── scripts/                 # Backend utility scripts
├── scheduler-frontend/          # Renamed from src/
│   ├── src/                     # Source code
│   │   ├── components/          # React components
│   │   ├── store/               # State management
│   │   ├── api/                 # API client
│   │   ├── utils/               # Utility functions
│   │   └── types/               # TypeScript type definitions
│   ├── tests/                   # Frontend tests
│   └── docs/                    # Frontend-specific documentation
├── docs/                        # Consolidated documentation
│   ├── architecture/            # System architecture
│   ├── requirements/            # Project requirements
│   ├── user-guides/             # User documentation
│   └── development/             # Development guides
├── scripts/                     # Project-level scripts
│   ├── setup/                   # Setup scripts
│   └── ci/                      # CI/CD scripts
├── data/                        # Sample and test data
│   ├── samples/                 # Sample datasets
│   └── fixtures/                # Test fixtures
└── .github/                     # GitHub specific files
    └── workflows/               # GitHub Actions workflows
```

### 2.2 Backend Reorganization

```
scheduler-backend/app/
├── api/                         # API endpoints
│   ├── routes/                  # API route definitions
│   ├── schemas/                 # Request/response schemas
│   └── dependencies/            # API dependencies
├── core/                        # Core scheduling logic
│   ├── constraints/             # Scheduling constraints
│   │   ├── hard_constraints/    # Hard constraints
│   │   └── soft_constraints/    # Soft constraints
│   ├── objectives/              # Optimization objectives
│   ├── solvers/                 # Solver implementations
│   │   ├── genetic/             # Genetic algorithm
│   │   ├── cp_sat/              # CP-SAT solver
│   │   └── experiments/         # Experimental solvers
│   └── validation/              # Solution validation
├── models/                      # Data models
│   ├── domain/                  # Domain models
│   ├── schemas/                 # Validation schemas
│   └── serializers/             # Data serializers
└── utils/                       # Utility functions
    ├── logging/                 # Logging utilities
    └── performance/             # Performance monitoring
```

### 2.3 Frontend Reorganization

```
scheduler-frontend/src/
├── components/                  # React components
│   ├── common/                  # Shared components
│   ├── layout/                  # Layout components
│   ├── forms/                   # Form components
│   ├── schedule-viewer/         # Schedule visualization
│   ├── dashboard/               # Analytics dashboard
│   └── solver/                  # Solver configuration
├── hooks/                       # Custom React hooks
├── store/                       # State management
│   ├── schedule/                # Schedule state
│   ├── dashboard/               # Dashboard state
│   └── ui/                      # UI state
├── api/                         # API client
│   ├── client.ts                # Base API client
│   ├── schedule.ts              # Schedule API
│   └── dashboard.ts             # Dashboard API
├── utils/                       # Utility functions
│   ├── formatting/              # Data formatting
│   ├── validation/              # Client-side validation
│   └── visualization/           # Visualization helpers
└── types/                       # TypeScript type definitions
    ├── api/                     # API types
    ├── domain/                  # Domain types
    └── store/                   # Store types
```

### 2.4 Documentation Reorganization

```
docs/
├── architecture/               # System architecture
│   ├── overview.md             # System overview
│   ├── backend.md              # Backend architecture
│   └── frontend.md             # Frontend architecture
├── requirements/               # Project requirements
│   ├── mvp.md                  # MVP requirements
│   └── constraints.md          # Scheduling constraints
├── user-guides/                # User documentation
│   ├── getting-started.md      # Getting started guide
│   ├── data-import.md          # Data import guide
│   └── schedule-creation.md    # Schedule creation guide
└── development/                # Development guides
    ├── setup.md                # Development setup
    ├── contributing.md         # Contribution guidelines
    └── testing.md              # Testing guidelines
```

## 3. Migration Strategy

### 3.1 Phased Implementation

To minimize disruption while ensuring steady progress, the reorganization will be implemented in three phases:

#### Phase 1: Foundation (1-2 days)
- Create the new top-level directory structure
- Setup `.gitignore` updates for generated files
- Establish the documentation framework
- Create script templates for migration

#### Phase 2: Component Migration (3-5 days)
- Migrate backend components in small, testable units
- Migrate frontend components in parallel
- Update import paths incrementally
- Run tests after each component migration

#### Phase 3: Cleanup and Finalization (1-2 days)
- Remove redundant files and directories
- Update all documentation references
- Verify all tests pass in the new structure
- Update CI/CD configuration

### 3.2 Migration Scripts

To automate and standardize the migration process, the following scripts will be developed:

1. **Directory Creator Script**
   - Creates the new directory structure
   - Sets up appropriate `.gitignore` files
   - Generates placeholder README files

2. **Backend Migration Script**
   - Migrates backend code to the new structure
   - Updates import paths
   - Runs tests to verify functionality

3. **Frontend Migration Script**
   - Migrates frontend code to the new structure
   - Updates import paths
   - Runs tests to verify functionality

4. **Documentation Migration Script**
   - Migrates documentation to the new structure
   - Updates internal links
   - Generates documentation index

### 3.3 Version Control Strategy

1. **Branch Strategy**
   - Create a dedicated `directory-reorganization` branch
   - Implement changes in small, atomic commits
   - Use pull requests to merge completed phases

2. **Commit Organization**
   - Group commits by component (e.g., "Reorganize backend constraints")
   - Include detailed descriptions of changes
   - Reference related issues or tasks

3. **Merge Approach**
   - Use squash merging to maintain a clean history
   - Thoroughly review changes before merging
   - Update documentation with each merge

## 4. File-Specific Migration Details

### 4.1 Backend Files

| Current Path | New Path | Migration Notes |
|--------------|----------|----------------|
| `scheduler-backend/app/scheduling/` | `scheduler-backend/app/core/` | Rename directory, update imports |
| `scheduler-backend/app/visualization/` | `scheduler-frontend/src/utils/visualization/` | Move to frontend, refactor API calls |
| `scheduler-backend/app/models.py` | `scheduler-backend/app/models/domain/` | Split into domain-specific models |
| `scheduler-backend/app/main.py` | `scheduler-backend/app/api/main.py` | Move to API directory |
| `scheduler-backend/app/routers/` | `scheduler-backend/app/api/routes/` | Rename and reorganize |

### 4.2 Frontend Files

| Current Path | New Path | Migration Notes |
|--------------|----------|----------------|
| `src/` | `scheduler-frontend/src/` | Move to new directory |
| `src/__tests__/` | `scheduler-frontend/tests/` | Move outside src directory |
| `src/components/Calendar.tsx` | `scheduler-frontend/src/components/schedule-viewer/ScheduleViewer.tsx` | Rename and move to dedicated directory |
| `src/store/` | `scheduler-frontend/src/store/` | Maintain structure, update imports |
| `src/lib/` | `scheduler-frontend/src/utils/` | Rename to utils for consistency |

### 4.3 Documentation Files

| Current Path | New Path | Migration Notes |
|--------------|----------|----------------|
| `memory-bank/*.md` | `docs/*/` | Categorize and move to appropriate directories |
| `memory-bank/implementationPhases/` | `docs/architecture/phases/` | Move to architecture section |
| `memory-bank/review/` | `docs/development/review/` | Move to development section |
| `scheduler-backend/README.md` | `docs/development/backend-setup.md` | Move to development section |

## 5. Risk Assessment and Mitigation

### 5.1 Identified Risks

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Breaking existing functionality | High | High | Comprehensive test suite, incremental changes |
| Merge conflicts | Medium | Medium | Coordinate changes, use feature branches |
| Path reference errors | High | Medium | Automated path updates, thorough testing |
| Documentation links breaking | High | Low | Update documentation links, use relative paths |
| CI/CD pipeline failures | Medium | High | Update CI configuration, test in isolation |

### 5.2 Mitigation Strategies

1. **Testing Strategy**
   - Run existing test suite after each migration step
   - Add tests for edge cases before migration
   - Create integration tests to verify cross-component functionality

2. **Rollback Plan**
   - Maintain the original directory structure in a separate branch
   - Create restore points before major changes
   - Document manual rollback steps for critical components

3. **Communication Plan**
   - Notify all team members before beginning migration
   - Document progress and blockers daily
   - Provide clear guidance on working during the transition

## 6. Implementation Checklist

### 6.1 Preparation Phase
- [ ] Create backup of current codebase
- [ ] Update `.gitignore` for generated files
- [ ] Create migration scripts
- [ ] Update CI/CD configuration

### 6.2 Backend Migration
- [ ] Create new backend directory structure
- [ ] Migrate core scheduling logic
- [ ] Migrate API endpoints
- [ ] Migrate models
- [ ] Migrate utils
- [ ] Run backend tests

### 6.3 Frontend Migration
- [ ] Create new frontend directory structure
- [ ] Migrate components
- [ ] Migrate store
- [ ] Migrate types
- [ ] Move visualization from backend
- [ ] Run frontend tests

### 6.4 Documentation Migration
- [ ] Set up documentation framework
- [ ] Categorize existing documentation
- [ ] Migrate content to new structure
- [ ] Create index and navigation
- [ ] Update internal links

### 6.5 Finalization
- [ ] Remove redundant files
- [ ] Update README files
- [ ] Verify all tests pass
- [ ] Create final pull request
- [ ] Update developer documentation

## 7. Timeline

| Phase | Tasks | Timeline | Dependencies |
|-------|-------|----------|--------------|
| Preparation | Create backup, scripts, configure git | Day 1 | None |
| Backend Migration | Migrate backend components | Days 2-3 | Preparation |
| Frontend Migration | Migrate frontend components | Days 4-5 | Preparation |
| Documentation Migration | Migrate and reorganize documentation | Day 6 | None |
| Testing and Verification | Verify all functionality | Day 7 | All previous phases |
| Finalization | Cleanup, final testing | Day 8 | All previous phases |

## 8. Success Criteria

The directory reorganization will be considered successful when:

1. All code is migrated to the new directory structure
2. All tests pass in the new structure
3. The CI/CD pipeline successfully builds and tests the code
4. Documentation is properly organized and accessible
5. No duplicate or redundant files exist
6. Development workflow is maintained or improved

## 9. Conclusion

This directory reorganization plan provides a structured approach to improving the organization and maintainability of the Gym Class Rotation Scheduler project. By following this plan, we will establish a more logical and scalable directory structure that separates concerns appropriately, reduces redundancy, and improves the overall developer experience.

The phased implementation approach ensures that we can make progress while minimizing disruption to ongoing development. The detailed migration steps and risk mitigation strategies address potential issues before they arise, ensuring a smooth transition to the new structure.
