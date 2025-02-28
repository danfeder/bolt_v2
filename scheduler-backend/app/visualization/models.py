"""Data models for visualization and dashboard components."""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class ChartDataPoint(BaseModel):
    """Data point for chart visualization."""
    x: Union[str, int, float]
    y: Union[int, float]
    category: Optional[str] = None
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "x": "Monday",
                "y": 3,
                "category": "Grade 1"
            }
        }
    }


class ChartDataSeries(BaseModel):
    """Data series for chart visualization."""
    name: str
    data: List[ChartDataPoint]
    color: Optional[str] = None
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "name": "Class Assignments",
                "data": [
                    {"x": "Monday", "y": 3},
                    {"x": "Tuesday", "y": 4},
                    {"x": "Wednesday", "y": 2}
                ],
                "color": "#4e79a7"
            }
        }
    }


class ChartData(BaseModel):
    """Chart data for visualization."""
    series: List[ChartDataSeries]
    title: str
    xAxisLabel: Optional[str] = None
    yAxisLabel: Optional[str] = None
    type: str = Field("bar", description="Chart type (bar, line, pie, heatmap)")
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "series": [
                    {
                        "name": "Class Assignments",
                        "data": [
                            {"x": "Monday", "y": 3},
                            {"x": "Tuesday", "y": 4},
                            {"x": "Wednesday", "y": 2}
                        ]
                    }
                ],
                "title": "Classes Per Day",
                "xAxisLabel": "Day of Week",
                "yAxisLabel": "Number of Classes",
                "type": "bar"
            }
        }
    }


class GradePeriodHeatmapCell(BaseModel):
    """Cell for grade-period heatmap visualization."""
    grade: str
    period: int
    value: int
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "grade": "Grade 1",
                "period": 1,
                "value": 3
            }
        }
    }


class ConstraintSatisfactionMetric(BaseModel):
    """Metric for constraint satisfaction visualization."""
    name: str
    satisfied: int
    total: int
    percentage: float
    category: str
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "name": "Preferred Periods",
                "satisfied": 45,
                "total": 60,
                "percentage": 75.0,
                "category": "Preferences"
            }
        }
    }


class ScheduleQualityMetrics(BaseModel):
    """Overall quality metrics for a schedule."""
    distribution_score: float
    preference_satisfaction: float
    workload_balance: float
    period_spread: float
    overall_score: float
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "distribution_score": 85.5,
                "preference_satisfaction": 78.3,
                "workload_balance": 92.1,
                "period_spread": 88.7,
                "overall_score": 86.2
            }
        }
    }


class ScheduleComparisonResult(BaseModel):
    """Comparison between two schedules."""
    metric_name: str
    baseline_value: float
    comparison_value: float
    difference: float
    percentage_change: float
    improvement: bool
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "metric_name": "Distribution Score",
                "baseline_value": 82.3,
                "comparison_value": 85.5,
                "difference": 3.2,
                "percentage_change": 3.89,
                "improvement": True
            }
        }
    }


class DashboardData(BaseModel):
    """Complete dashboard data."""
    schedule_id: str
    timestamp: str
    quality_metrics: ScheduleQualityMetrics
    daily_distribution: ChartData
    period_distribution: ChartData
    grade_distribution: ChartData
    constraint_satisfaction: List[ConstraintSatisfactionMetric]
    grade_period_heatmap: List[GradePeriodHeatmapCell]
    
    model_config = {
        'json_schema_extra': {
            "example": {
                "schedule_id": "schedule_2025-02-27",
                "timestamp": "2025-02-27T15:30:45Z",
                "quality_metrics": {
                    "distribution_score": 85.5,
                    "preference_satisfaction": 78.3,
                    "workload_balance": 92.1,
                    "period_spread": 88.7,
                    "overall_score": 86.2
                },
                "daily_distribution": {
                    "series": [],
                    "title": "Classes Per Day",
                    "xAxisLabel": "Day of Week",
                    "yAxisLabel": "Number of Classes",
                    "type": "bar"
                },
                "period_distribution": {
                    "series": [],
                    "title": "Classes Per Period",
                    "xAxisLabel": "Period",
                    "yAxisLabel": "Number of Classes",
                    "type": "bar"
                },
                "grade_distribution": {
                    "series": [],
                    "title": "Classes Per Grade",
                    "xAxisLabel": "Grade",
                    "yAxisLabel": "Number of Classes",
                    "type": "bar"
                },
                "constraint_satisfaction": [],
                "grade_period_heatmap": []
            }
        }
    }