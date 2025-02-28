"""Dashboard visualization for schedule analysis."""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import statistics
from uuid import uuid4

from ..models import ScheduleResponse, ScheduleAssignment, Class
from ..scheduling.core import SchedulerContext
from .models import (
    ChartData, 
    ChartDataSeries, 
    ChartDataPoint,
    GradePeriodHeatmapCell,
    ConstraintSatisfactionMetric,
    ScheduleQualityMetrics,
    ScheduleComparisonResult,
    DashboardData
)

# Define colors for chart visualizations
CHART_COLORS = [
    "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
]

def create_dashboard_data(
    schedule: ScheduleResponse,
    classes: List[Class],
    context: Optional[SchedulerContext] = None,
) -> DashboardData:
    """
    Create a complete dashboard data object from a schedule.
    
    Args:
        schedule: The schedule response object
        classes: List of class objects with metadata
        context: Optional scheduler context with additional info
        
    Returns:
        DashboardData object with all charts and metrics
    """
    # Create unique identifier for this schedule
    schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
    timestamp = datetime.now().isoformat()
    
    # Get assignments
    assignments = schedule.assignments
    
    # Create daily distribution chart
    daily_distribution = create_daily_distribution_chart(assignments)
    
    # Create period distribution chart
    period_distribution = create_period_distribution_chart(assignments)
    
    # Create grade distribution chart
    grade_distribution = create_grade_distribution_chart(assignments, classes)
    
    # Create grade-period heatmap
    grade_period_heatmap = create_grade_period_heatmap(assignments, classes)
    
    # Create constraint satisfaction metrics
    constraint_satisfaction = calculate_constraint_satisfaction(assignments, classes, context)
    
    # Calculate overall quality metrics
    quality_metrics = calculate_quality_metrics(assignments, classes, context, schedule.metadata)
    
    return DashboardData(
        schedule_id=schedule_id,
        timestamp=timestamp,
        quality_metrics=quality_metrics,
        daily_distribution=daily_distribution,
        period_distribution=period_distribution,
        grade_distribution=grade_distribution,
        constraint_satisfaction=constraint_satisfaction,
        grade_period_heatmap=grade_period_heatmap
    )


def create_daily_distribution_chart(assignments: List[ScheduleAssignment]) -> ChartData:
    """
    Create a chart showing class distribution by day of week.
    
    Args:
        assignments: List of schedule assignments
        
    Returns:
        ChartData for daily distribution
    """
    # Count assignments per day
    days_map = {
        0: "Monday",
        1: "Tuesday", 
        2: "Wednesday",
        3: "Thursday",
        4: "Friday"
    }
    
    # Group by day of week
    by_day = defaultdict(int)
    for assignment in assignments:
        # Parse date to get day of week
        date = datetime.fromisoformat(assignment.date)
        day_name = days_map.get(date.weekday(), str(date.weekday()))
        by_day[day_name] += 1
    
    # Create data points in order
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    data_points = [
        ChartDataPoint(x=day, y=by_day.get(day, 0))
        for day in day_order if day in by_day
    ]
    
    # Create chart data
    series = [
        ChartDataSeries(
            name="Classes",
            data=data_points,
            color=CHART_COLORS[0]
        )
    ]
    
    return ChartData(
        series=series,
        title="Classes Per Day of Week",
        xAxisLabel="Day of Week",
        yAxisLabel="Number of Classes",
        type="bar"
    )


def create_period_distribution_chart(assignments: List[ScheduleAssignment]) -> ChartData:
    """
    Create a chart showing class distribution by period.
    
    Args:
        assignments: List of schedule assignments
        
    Returns:
        ChartData for period distribution
    """
    # Count assignments per period
    by_period = defaultdict(int)
    for assignment in assignments:
        period = assignment.timeSlot.period
        by_period[period] += 1
    
    # Create data points in order
    data_points = [
        ChartDataPoint(x=f"Period {period}", y=count)
        for period, count in sorted(by_period.items())
    ]
    
    # Create chart data
    series = [
        ChartDataSeries(
            name="Classes",
            data=data_points,
            color=CHART_COLORS[1]
        )
    ]
    
    return ChartData(
        series=series,
        title="Classes Per Period",
        xAxisLabel="Period",
        yAxisLabel="Number of Classes",
        type="bar"
    )


def create_grade_distribution_chart(
    assignments: List[ScheduleAssignment],
    classes: List[Class]
) -> ChartData:
    """
    Create a chart showing class distribution by grade.
    
    Args:
        assignments: List of schedule assignments
        classes: List of class objects with grade information
        
    Returns:
        ChartData for grade distribution
    """
    # Create mapping of class name to grade
    class_to_grade = {
        class_obj.name: class_obj.grade
        for class_obj in classes
    }
    
    # Count assignments per grade
    by_grade = defaultdict(int)
    for assignment in assignments:
        grade = class_to_grade.get(assignment.name, "Unknown")
        by_grade[grade] += 1
    
    # Create data points
    # Map grades to numeric values for sorting
    grade_order = {
        "Pre-K": 0,
        "K": 1
    }
    # Add numeric grades
    for i in range(1, 6):
        grade_order[str(i)] = i + 1
    
    # Sort grades by order
    sorted_grades = sorted(
        by_grade.keys(), 
        key=lambda g: grade_order.get(g, 100)  # Unknown grades at the end
    )
    
    data_points = [
        ChartDataPoint(x=grade, y=by_grade[grade])
        for grade in sorted_grades
    ]
    
    # Create chart data
    series = [
        ChartDataSeries(
            name="Classes",
            data=data_points,
            color=CHART_COLORS[2]
        )
    ]
    
    return ChartData(
        series=series,
        title="Classes Per Grade",
        xAxisLabel="Grade",
        yAxisLabel="Number of Classes",
        type="bar"
    )


def create_grade_period_heatmap(
    assignments: List[ScheduleAssignment],
    classes: List[Class]
) -> List[GradePeriodHeatmapCell]:
    """
    Create a heatmap showing grade distribution across periods.
    
    Args:
        assignments: List of schedule assignments
        classes: List of class objects with grade information
        
    Returns:
        List of heatmap cells for grade-period distribution
    """
    # Create mapping of class name to grade
    class_to_grade = {
        class_obj.name: class_obj.grade
        for class_obj in classes
    }
    
    # Count assignments per grade and period
    by_grade_period = defaultdict(lambda: defaultdict(int))
    for assignment in assignments:
        grade = class_to_grade.get(assignment.name, "Unknown")
        period = assignment.timeSlot.period
        by_grade_period[grade][period] += 1
    
    # Create heatmap cells
    heatmap_cells = []
    for grade, periods in by_grade_period.items():
        for period, count in periods.items():
            heatmap_cells.append(
                GradePeriodHeatmapCell(
                    grade=grade,
                    period=period,
                    value=count
                )
            )
    
    return heatmap_cells


def calculate_constraint_satisfaction(
    assignments: List[ScheduleAssignment],
    classes: List[Class],
    context: Optional[SchedulerContext] = None
) -> List[ConstraintSatisfactionMetric]:
    """
    Calculate constraint satisfaction metrics.
    
    Args:
        assignments: List of schedule assignments
        classes: List of class objects with constraint info
        context: Optional scheduler context with additional info
        
    Returns:
        List of constraint satisfaction metrics
    """
    metrics = []
    
    # Create mapping of class name to class object
    class_by_name = {
        class_obj.name: class_obj
        for class_obj in classes
    }
    
    # Create mapping of assignments by class name
    assignments_by_class = defaultdict(list)
    for assignment in assignments:
        assignments_by_class[assignment.name].append(assignment)
    
    # Check required periods satisfaction
    required_satisfied = 0
    required_total = 0
    
    for class_name, class_obj in class_by_name.items():
        if hasattr(class_obj, "weeklySchedule") and class_obj.weeklySchedule.requiredPeriods:
            required_periods = class_obj.weeklySchedule.requiredPeriods
            required_total += len(required_periods)
            
            # Check if each required period is satisfied
            class_assignments = assignments_by_class.get(class_name, [])
            for required in required_periods:
                # Check if this required period is in the assignments
                if any(
                    a.timeSlot.dayOfWeek == required.dayOfWeek and 
                    a.timeSlot.period == required.period
                    for a in class_assignments
                ):
                    required_satisfied += 1
    
    if required_total > 0:
        metrics.append(
            ConstraintSatisfactionMetric(
                name="Required Periods",
                satisfied=required_satisfied,
                total=required_total,
                percentage=round(100 * required_satisfied / required_total, 1),
                category="Hard Constraints"
            )
        )
    
    # Check preferred periods satisfaction
    preferred_satisfied = 0
    preferred_total = 0
    
    for class_name, class_obj in class_by_name.items():
        if hasattr(class_obj, "weeklySchedule") and class_obj.weeklySchedule.preferredPeriods:
            preferred_periods = class_obj.weeklySchedule.preferredPeriods
            preferred_total += len(preferred_periods)
            
            # Check if each preferred period is satisfied
            class_assignments = assignments_by_class.get(class_name, [])
            for preferred in preferred_periods:
                # Check if this preferred period is in the assignments
                if any(
                    a.timeSlot.dayOfWeek == preferred.dayOfWeek and 
                    a.timeSlot.period == preferred.period
                    for a in class_assignments
                ):
                    preferred_satisfied += 1
    
    if preferred_total > 0:
        metrics.append(
            ConstraintSatisfactionMetric(
                name="Preferred Periods",
                satisfied=preferred_satisfied,
                total=preferred_total,
                percentage=round(100 * preferred_satisfied / preferred_total, 1),
                category="Preferences"
            )
        )
    
    # Check avoided periods satisfaction (opposite logic - we want to avoid these)
    avoided_satisfied = 0
    avoided_total = 0
    
    for class_name, class_obj in class_by_name.items():
        if hasattr(class_obj, "weeklySchedule") and class_obj.weeklySchedule.avoidPeriods:
            avoid_periods = class_obj.weeklySchedule.avoidPeriods
            avoided_total += len(avoid_periods)
            
            # Check if each avoid period is not used
            class_assignments = assignments_by_class.get(class_name, [])
            for avoid in avoid_periods:
                # Check if this avoid period is NOT in the assignments
                if not any(
                    a.timeSlot.dayOfWeek == avoid.dayOfWeek and 
                    a.timeSlot.period == avoid.period
                    for a in class_assignments
                ):
                    avoided_satisfied += 1
    
    if avoided_total > 0:
        metrics.append(
            ConstraintSatisfactionMetric(
                name="Avoided Periods",
                satisfied=avoided_satisfied,
                total=avoided_total,
                percentage=round(100 * avoided_satisfied / avoided_total, 1),
                category="Preferences"
            )
        )
    
    # Add relaxation metrics if available
    if context and hasattr(context, 'relaxation_controller'):
        relaxation_controller = context.relaxation_controller
        if relaxation_controller:
            # Get constraints that were relaxed
            relaxed_constraints = 0
            total_constraints = 0
            
            relaxation_status = relaxation_controller.get_relaxation_status()
            for constraint_name, constraint_info in relaxation_status.get('constraints', {}).items():
                total_constraints += 1
                if constraint_info.get('current_relaxation_level', 'NONE') != 'NONE':
                    relaxed_constraints += 1
            
            if total_constraints > 0:
                metrics.append(
                    ConstraintSatisfactionMetric(
                        name="Constraints Without Relaxation",
                        satisfied=total_constraints - relaxed_constraints,
                        total=total_constraints,
                        percentage=round(100 * (total_constraints - relaxed_constraints) / total_constraints, 1),
                        category="Constraint Relaxation"
                    )
                )
    
    return metrics


def calculate_quality_metrics(
    assignments: List[ScheduleAssignment],
    classes: List[Class],
    context: Optional[SchedulerContext] = None,
    metadata: Any = None
) -> ScheduleQualityMetrics:
    """
    Calculate overall schedule quality metrics.
    
    Args:
        assignments: List of schedule assignments
        classes: List of class objects with constraint info
        context: Optional scheduler context with additional info
        metadata: Optional schedule metadata
        
    Returns:
        ScheduleQualityMetrics object
    """
    # Extract distribution score from metadata if available
    distribution_score = 0.0
    if metadata and hasattr(metadata, 'distribution') and metadata.distribution:
        distribution_score = min(100, max(0, 100 + metadata.distribution.totalScore / 1000))
    else:
        # Calculate basic distribution metrics
        distribution_score = calculate_distribution_score(assignments)
    
    # Calculate preference satisfaction from constraint metrics
    constraint_metrics = calculate_constraint_satisfaction(assignments, classes, context)
    preference_metrics = [m for m in constraint_metrics if m.category == "Preferences"]
    
    preference_satisfaction = 0.0
    if preference_metrics:
        # Average the percentage values
        preference_satisfaction = sum(m.percentage for m in preference_metrics) / len(preference_metrics)
    
    # Calculate workload balance
    workload_balance = calculate_workload_balance(assignments)
    
    # Calculate period spread (even distribution across periods)
    period_spread = calculate_period_spread(assignments)
    
    # Calculate overall score (weighted average)
    weights = {
        "distribution_score": 0.35,
        "preference_satisfaction": 0.30,
        "workload_balance": 0.20,
        "period_spread": 0.15
    }
    
    overall_score = (
        distribution_score * weights["distribution_score"] +
        preference_satisfaction * weights["preference_satisfaction"] +
        workload_balance * weights["workload_balance"] +
        period_spread * weights["period_spread"]
    )
    
    return ScheduleQualityMetrics(
        distribution_score=round(distribution_score, 1),
        preference_satisfaction=round(preference_satisfaction, 1),
        workload_balance=round(workload_balance, 1),
        period_spread=round(period_spread, 1),
        overall_score=round(overall_score, 1)
    )


def calculate_distribution_score(assignments: List[ScheduleAssignment]) -> float:
    """
    Calculate a distribution score based on how evenly classes are distributed.
    
    Args:
        assignments: List of schedule assignments
        
    Returns:
        Distribution score (0-100, higher is better)
    """
    # Group by day
    by_day = defaultdict(int)
    for assignment in assignments:
        date = datetime.fromisoformat(assignment.date)
        by_day[date.date()] += 1
    
    # Group by week
    by_week = defaultdict(int)
    for assignment in assignments:
        date = datetime.fromisoformat(assignment.date)
        week_num = date.isocalendar()[1]  # ISO week number
        by_week[week_num] += 1
    
    # Calculate variance metrics
    day_counts = list(by_day.values())
    week_counts = list(by_week.values())
    
    # Calculate variances
    day_variance = statistics.variance(day_counts) if len(day_counts) > 1 else 0
    week_variance = statistics.variance(week_counts) if len(week_counts) > 1 else 0
    
    # Normalize variances (lower is better)
    # For a perfect distribution, variance would be 0
    max_day_variance = 25  # Theoretical maximum for typical schedules
    max_week_variance = 100  # Theoretical maximum for typical schedules
    
    day_score = 100 * (1 - min(day_variance / max_day_variance, 1.0))
    week_score = 100 * (1 - min(week_variance / max_week_variance, 1.0))
    
    # Combine scores (weighted)
    distribution_score = 0.6 * day_score + 0.4 * week_score
    
    return distribution_score


def calculate_workload_balance(assignments: List[ScheduleAssignment]) -> float:
    """
    Calculate workload balance score based on how evenly classes are distributed by teacher.
    
    Args:
        assignments: List of schedule assignments
        
    Returns:
        Workload balance score (0-100, higher is better)
    """
    # Group by class (proxy for teacher)
    by_class = defaultdict(int)
    for assignment in assignments:
        by_class[assignment.name] += 1
    
    # Calculate variance in class assignments
    class_counts = list(by_class.values())
    
    if len(class_counts) <= 1:
        return 100.0  # Perfect balance with only one class
    
    variance = statistics.variance(class_counts)
    
    # Normalize variance (lower is better)
    # For a perfect distribution, variance would be 0
    max_variance = 25  # Theoretical maximum for typical schedules
    
    workload_balance = 100 * (1 - min(variance / max_variance, 1.0))
    
    return workload_balance


def calculate_period_spread(assignments: List[ScheduleAssignment]) -> float:
    """
    Calculate period spread score based on how evenly classes are distributed across periods.
    
    Args:
        assignments: List of schedule assignments
        
    Returns:
        Period spread score (0-100, higher is better)
    """
    # Group by period
    by_period = defaultdict(int)
    for assignment in assignments:
        by_period[assignment.timeSlot.period] += 1
    
    # Calculate variance in period assignments
    period_counts = list(by_period.values())
    
    if len(period_counts) <= 1:
        return 100.0  # Perfect spread with only one period
    
    variance = statistics.variance(period_counts)
    
    # Normalize variance (lower is better)
    # For a perfect distribution, variance would be 0
    max_variance = 25  # Theoretical maximum for typical schedules
    
    period_spread = 100 * (1 - min(variance / max_variance, 1.0))
    
    return period_spread


def compare_schedules(
    baseline: ScheduleResponse,
    comparison: ScheduleResponse,
    classes: List[Class],
    context: Optional[SchedulerContext] = None
) -> List[ScheduleComparisonResult]:
    """
    Compare two schedules and return detailed comparison metrics.
    
    Args:
        baseline: Baseline schedule response
        comparison: Comparison schedule response
        classes: List of class objects with metadata
        context: Optional scheduler context with additional info
        
    Returns:
        List of comparison results for different metrics
    """
    # Calculate metrics for both schedules
    baseline_metrics = calculate_quality_metrics(
        baseline.assignments, classes, context, baseline.metadata
    )
    comparison_metrics = calculate_quality_metrics(
        comparison.assignments, classes, context, comparison.metadata
    )
    
    # Compare each metric
    results = []
    
    # Distribution score
    results.append(
        ScheduleComparisonResult(
            metric_name="Distribution Score",
            baseline_value=baseline_metrics.distribution_score,
            comparison_value=comparison_metrics.distribution_score,
            difference=comparison_metrics.distribution_score - baseline_metrics.distribution_score,
            percentage_change=calculate_percentage_change(
                baseline_metrics.distribution_score, 
                comparison_metrics.distribution_score
            ),
            improvement=comparison_metrics.distribution_score > baseline_metrics.distribution_score
        )
    )
    
    # Preference satisfaction
    results.append(
        ScheduleComparisonResult(
            metric_name="Preference Satisfaction",
            baseline_value=baseline_metrics.preference_satisfaction,
            comparison_value=comparison_metrics.preference_satisfaction,
            difference=comparison_metrics.preference_satisfaction - baseline_metrics.preference_satisfaction,
            percentage_change=calculate_percentage_change(
                baseline_metrics.preference_satisfaction, 
                comparison_metrics.preference_satisfaction
            ),
            improvement=comparison_metrics.preference_satisfaction > baseline_metrics.preference_satisfaction
        )
    )
    
    # Workload balance
    results.append(
        ScheduleComparisonResult(
            metric_name="Workload Balance",
            baseline_value=baseline_metrics.workload_balance,
            comparison_value=comparison_metrics.workload_balance,
            difference=comparison_metrics.workload_balance - baseline_metrics.workload_balance,
            percentage_change=calculate_percentage_change(
                baseline_metrics.workload_balance, 
                comparison_metrics.workload_balance
            ),
            improvement=comparison_metrics.workload_balance > baseline_metrics.workload_balance
        )
    )
    
    # Period spread
    results.append(
        ScheduleComparisonResult(
            metric_name="Period Spread",
            baseline_value=baseline_metrics.period_spread,
            comparison_value=comparison_metrics.period_spread,
            difference=comparison_metrics.period_spread - baseline_metrics.period_spread,
            percentage_change=calculate_percentage_change(
                baseline_metrics.period_spread, 
                comparison_metrics.period_spread
            ),
            improvement=comparison_metrics.period_spread > baseline_metrics.period_spread
        )
    )
    
    # Overall score
    results.append(
        ScheduleComparisonResult(
            metric_name="Overall Score",
            baseline_value=baseline_metrics.overall_score,
            comparison_value=comparison_metrics.overall_score,
            difference=comparison_metrics.overall_score - baseline_metrics.overall_score,
            percentage_change=calculate_percentage_change(
                baseline_metrics.overall_score, 
                comparison_metrics.overall_score
            ),
            improvement=comparison_metrics.overall_score > baseline_metrics.overall_score
        )
    )
    
    return results


def calculate_percentage_change(baseline: float, comparison: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        baseline: Baseline value
        comparison: Comparison value
        
    Returns:
        Percentage change (can be positive or negative)
    """
    if baseline == 0:
        return 0.0 if comparison == 0 else 100.0
        
    return round(100 * (comparison - baseline) / abs(baseline), 2)