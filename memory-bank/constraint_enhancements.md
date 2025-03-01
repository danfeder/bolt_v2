# Scheduling Constraint Enhancements

This document outlines planned enhancements to the scheduling constraint system for the gym class rotation scheduler. These improvements are designed to address specific requirements for scheduling 33 classes through a single gym facility with one teacher.

## 1. Teacher Workload Management

### Consecutive Classes Control
**Priority: High**

**Description:**  
Implement controls for consecutive class scheduling to ensure appropriate teacher breaks while maintaining scheduling efficiency.

**Implementation:**
1. Add a togglable constraint `AllowConsecutiveClasses` that permits exactly 2 classes back-to-back
2. Create a hard constraint `MaxConsecutiveClasses` that strictly prevents 3 or more consecutive classes
3. Incorporate into the `validate()` method of the chromosome class and fitness calculation

**Required Changes:**
- Create new constraint class in `constraints/teacher_workload.py`
- Extend chromosome validation to check for consecutive class sequences
- Add configuration option in `config.py`
- Update UnifiedSolver to include the new constraint

**Success Criteria:**
- When enabled, schedules may contain pairs of back-to-back classes
- No schedule ever contains 3 consecutive classes without breaks
- Toggle works correctly to disallow even 2 consecutive classes when turned off

## 2. Grade-Level Grouping

### Similarity Preference System
**Priority: Medium**

**Description:**  
Enhance scheduling to prefer similar grade levels in consecutive periods, reducing equipment changes and activity transitions.

**Implementation:**
1. Define grade levels or groups in class definitions
2. Create a soft constraint (objective) that rewards scheduling similar grades consecutively
3. Add configurable weights for the similarity bonus

**Required Changes:**
- Extend `Class` model to include grade level information
- Create new objective in `objectives/grade_grouping.py`
- Add weighting configuration in `config.py`
- Update fitness calculation to consider grade grouping score

**Success Criteria:**
- Similar grade levels appear clustered in generated schedules
- Higher weight values result in more pronounced clustering
- Performance remains acceptable with the additional objective

## 3. Weight Tuning System

### Adaptive Weight Optimization
**Priority: Medium-High**

**Description:**  
Create a meta-optimization system that automatically tunes constraint weights to produce better schedules.

**Implementation:**
1. Develop a meta-genetic algorithm that optimizes constraint weights
2. Create a composite quality score that evaluates overall schedule quality
3. Run multiple schedule generations with different weight configurations
4. Allow manual override of discovered weights

**Required Changes:**
- Create new module `genetic/meta_optimizer.py`
- Implement weight chromosome representation
- Develop evaluation function for weight configurations
- Add configuration for meta-optimization parameters
- Create interface for viewing and applying discovered weights

**Success Criteria:**
- System discovers weight configurations that produce better schedules
- Performance improvement in constraint satisfaction vs. manual weights
- Clear reporting of which weights produce which improvements

## 4. Runtime Constraint Relaxation

### Hierarchical Relaxation System
**Priority: Medium**

**Description:**  
Implement a system that intelligently relaxes less important constraints when no perfect solution exists.

**Implementation:**
1. Define a relaxation hierarchy for constraints
2. Create a relaxation controller that progressively loosens constraints
3. Implement feedback mechanism to report which constraints were relaxed
4. Add "never relax" flags for critical constraints

**Required Changes:**
- Create new module `constraints/relaxation.py`
- Extend constraint classes with relaxation methods
- Modify solver to attempt increasingly relaxed solutions
- Add reporting mechanism for relaxation decisions

**Success Criteria:**
- System produces workable schedules even with difficult constraint sets
- Relaxation follows the defined hierarchy
- Critical constraints are never violated
- Clear reporting of which constraints were relaxed and by how much

## 5. Seasonal Adaptations (Deferred to Future Release)

### Season-Specific Scheduling
**Priority: Low-Medium**
**Status: Deferred to future development cycle**

**Description:**  
Add season profiles with different constraint settings to accommodate seasonal variations in gym activities.

**Implementation (Planned for Future):**
1. Create season profile configuration system
2. Define constraint variations for different seasons
3. Implement season selection in the scheduling interface
4. Allow season-specific facility availability settings

**Required Changes (Future Implementation):**
- Create new module `config/seasons.py`
- Extend schedule request model to include season information
- Modify constraint application based on selected season
- Update configuration interface for season profiles

**Success Criteria (For Future Evaluation):**
- Different seasons produce appropriately different schedules
- Season-specific constraints are correctly applied
- User can easily switch between season profiles

**Deferral Rationale:**
This feature has been deferred to focus on higher priority functionality. Current implementation will proceed without seasonal adaptation support, with this feature planned for a future release cycle.

## 6. Schedule Analysis Dashboard ✅

### Constraint Satisfaction Visualization
**Priority: Low**
**Status: Completed**

**Description:**  
Create a dashboard that visualizes constraint satisfaction levels and provides schedule quality metrics.

**Implementation (Completed):**
1. Created metrics for various aspects of schedule quality
2. Developed visualization components for constraint satisfaction
3. Implemented A/B comparison for different schedules
4. Built API endpoints for exploring schedule properties

**Changes Made:**
- Created new module `visualization/dashboard.py` with chart generation functions
- Added dashboard data models in `visualization/models.py`
- Implemented constraint satisfaction metrics and quality scoring
- Built API routes for dashboard access in `visualization/routes.py`
- Created test suite for dashboard functionality

**Success Criteria (Achieved):**
- Dashboard provides clear insights into schedule quality through multiple visualizations
- Metrics accurately reflect constraint satisfaction with percentage-based scoring
- Schedule comparisons highlight meaningful differences across key metrics
- API supports intuitive data exploration with chart-specific endpoints

## Implementation Timeline

Phase 1 (High Priority): ✅
- Teacher Workload Management
- Weight Tuning System

Phase 2 (Medium Priority): ✅
- Grade-Level Grouping
- Runtime Constraint Relaxation

Phase 3 (Lower Priority): ✅
- Schedule Analysis Dashboard ✅

Phase 4 (Future Release):
- Seasonal Adaptations (deferred to future development cycle)

## Integration with Genetic Algorithm

These enhancements will leverage and extend the genetic algorithm optimization system we have implemented. The adaptive nature of the genetic algorithm makes it particularly well-suited for these enhancements, as it can effectively navigate the complex solution space created by these additional constraints.

The parallel processing and advanced crossover methods recently implemented will be especially valuable for the weight tuning system and constraint relaxation features, which require exploring multiple potential solutions efficiently.