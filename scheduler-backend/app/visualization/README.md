# Schedule Analysis Dashboard

This directory contains the Schedule Analysis Dashboard implementation for the gym rotation scheduler.

## Overview

The Schedule Analysis Dashboard provides visualizations and metrics to evaluate the quality of generated schedules. It allows you to:

1. Analyze schedule quality across multiple dimensions
2. Visualize the distribution of classes by day, period, and grade
3. Track constraint satisfaction rates
4. Compare different schedules to identify improvements

## API Endpoints

The dashboard exposes the following API endpoints:

### POST /dashboard/analyze

Analyze a schedule and generate dashboard data.

**Parameters:**
- `request` (body): Schedule request to analyze
- `solver_type` (query): Solver type to use (`stable` or `dev`)

**Returns:**
- Complete dashboard data with visualizations and metrics

### GET /dashboard/history

Get list of previously analyzed schedules.

**Returns:**
- List of schedule history entries with metadata

### GET /dashboard/metrics/{schedule_id}

Get quality metrics for a specific schedule.

**Parameters:**
- `schedule_id` (path): ID of schedule to get metrics for

**Returns:**
- Schedule quality metrics

### GET /dashboard/chart/{chart_type}/{schedule_id}

Get specific chart data for a schedule.

**Parameters:**
- `chart_type` (path): Type of chart (`daily`, `period`, `grade`)
- `schedule_id` (path): ID of schedule to get chart for

**Returns:**
- Chart data for the specified chart type

### POST /dashboard/compare

Compare two schedules and return detailed comparison metrics.

**Parameters:**
- `baseline_id` (query): ID of baseline schedule
- `comparison_id` (query): ID of comparison schedule

**Returns:**
- List of comparison results for different metrics

## Metrics Calculated

The dashboard calculates the following quality metrics:

1. **Distribution Score** - How evenly classes are distributed across days and weeks
2. **Preference Satisfaction** - Percentage of preferred periods satisfied
3. **Workload Balance** - How evenly workload is distributed across teachers/classes
4. **Period Spread** - How evenly classes are distributed across periods
5. **Overall Score** - Weighted combination of the above metrics

## Visualizations

The dashboard provides the following visualizations:

1. **Daily Distribution Chart** - Bar chart showing classes per day of week
2. **Period Distribution Chart** - Bar chart showing classes per period
3. **Grade Distribution Chart** - Bar chart showing classes per grade
4. **Grade-Period Heatmap** - Heatmap showing grade distribution across periods

## Usage Example

```python
# Analyze a schedule
response = client.post(
    "/dashboard/analyze",
    json=schedule_request.dict(),
    params={"solver_type": "stable"}
)
dashboard_data = response.json()
schedule_id = dashboard_data["schedule_id"]

# Get quality metrics
metrics_response = client.get(f"/dashboard/metrics/{schedule_id}")
quality_metrics = metrics_response.json()

# Get daily distribution chart
chart_response = client.get(f"/dashboard/chart/daily/{schedule_id}")
daily_chart = chart_response.json()

# Compare with another schedule
comparison_response = client.post(
    "/dashboard/compare",
    params={
        "baseline_id": baseline_id,
        "comparison_id": schedule_id
    }
)
comparison_results = comparison_response.json()
```

## Development

To add new metrics or visualizations:

1. Add new model classes in `models.py`
2. Implement calculation functions in `dashboard.py`
3. Add new API endpoints in `routes.py`
4. Add tests in `tests/unit/test_dashboard.py` and `tests/integration/test_dashboard_api.py`