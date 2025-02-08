import pytest
import time
import psutil
import os
from datetime import datetime, timedelta
from app.scheduler import create_schedule_dev
from app.models import ScheduleConstraints
from tests.utils.generators import (
    ClassGenerator,
    TeacherAvailabilityGenerator,
    ScheduleRequestGenerator
)
from tests.utils.assertions import assert_valid_schedule

def measure_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert bytes to MB

def test_small_dataset_performance():
    """Test performance with a small dataset (5-10 classes)"""
    # Create schedule request with 8 classes
    request = ScheduleRequestGenerator.create_request(
        num_classes=8,
        num_weeks=2,
        constraints=ScheduleConstraints(
            maxClassesPerDay=3,
            maxClassesPerWeek=8,
            minPeriodsPerWeek=1,
            maxConsecutiveClasses=1,
            consecutiveClassesRule="hard"
        )
    )
    
    # Measure initial memory
    start_memory = measure_memory_usage()
    
    # Time the schedule generation
    start_time = time.time()
    response = create_schedule_dev(request)
    end_time = time.time()
    
    # Measure final memory
    end_memory = measure_memory_usage()
    
    # Calculate metrics
    duration_ms = int((end_time - start_time) * 1000)
    memory_increase = end_memory - start_memory
    
    # Verify schedule is valid
    assert_valid_schedule(response, request)
    
    # Assert performance meets requirements
    assert duration_ms < 5000, f"Small dataset took too long: {duration_ms}ms"
    assert memory_increase < 100, f"Memory usage too high: {memory_increase}MB increase"
    
    print(f"\nSmall Dataset Performance:")
    print(f"Duration: {duration_ms}ms")
    print(f"Memory Increase: {memory_increase:.2f}MB")

def test_medium_dataset_performance():
    """Test performance with a medium dataset (20-30 classes)"""
    # Create schedule request with 25 classes
    request = ScheduleRequestGenerator.create_request(
        num_classes=25,
        num_weeks=3,
        constraints=ScheduleConstraints(
            maxClassesPerDay=5,
            maxClassesPerWeek=15,
            minPeriodsPerWeek=2,
            maxConsecutiveClasses=2,
            consecutiveClassesRule="soft"
        )
    )
    
    # Measure initial memory
    start_memory = measure_memory_usage()
    
    # Time the schedule generation
    start_time = time.time()
    response = create_schedule_dev(request)
    end_time = time.time()
    
    # Measure final memory
    end_memory = measure_memory_usage()
    
    # Calculate metrics
    duration_ms = int((end_time - start_time) * 1000)
    memory_increase = end_memory - start_memory
    
    # Verify schedule is valid
    assert_valid_schedule(response, request)
    
    # Assert performance meets requirements
    assert duration_ms < 15000, f"Medium dataset took too long: {duration_ms}ms"
    assert memory_increase < 250, f"Memory usage too high: {memory_increase}MB increase"
    
    print(f"\nMedium Dataset Performance:")
    print(f"Duration: {duration_ms}ms")
    print(f"Memory Increase: {memory_increase:.2f}MB")

def test_large_dataset_performance():
    """Test performance with a large dataset (50+ classes)"""
    # Create schedule request with 50 classes
    request = ScheduleRequestGenerator.create_request(
        num_classes=50,
        num_weeks=4,
        constraints=ScheduleConstraints(
            maxClassesPerDay=8,
            maxClassesPerWeek=25,
            minPeriodsPerWeek=3,
            maxConsecutiveClasses=2,
            consecutiveClassesRule="soft"
        )
    )
    
    # Measure initial memory
    start_memory = measure_memory_usage()
    
    # Time the schedule generation
    start_time = time.time()
    response = create_schedule_dev(request)
    end_time = time.time()
    
    # Measure final memory
    end_memory = measure_memory_usage()
    
    # Calculate metrics
    duration_ms = int((end_time - start_time) * 1000)
    memory_increase = end_memory - start_memory
    
    # Verify schedule is valid
    assert_valid_schedule(response, request)
    
    # Assert performance meets requirements
    assert duration_ms < 30000, f"Large dataset took too long: {duration_ms}ms"
    assert memory_increase < 500, f"Memory usage too high: {memory_increase}MB increase"
    
    print(f"\nLarge Dataset Performance:")
    print(f"Duration: {duration_ms}ms")
    print(f"Memory Increase: {memory_increase:.2f}MB")

def test_solver_convergence():
    """Test how quickly the solver converges to a solution with increasing complexity"""
    class_counts = [5, 10, 15, 20, 25]
    convergence_times = []
    
    for num_classes in class_counts:
        request = ScheduleRequestGenerator.create_request(
            num_classes=num_classes,
            num_weeks=2,
            constraints=ScheduleConstraints(
                maxClassesPerDay=5,
                maxClassesPerWeek=15,
                minPeriodsPerWeek=1,
                maxConsecutiveClasses=2,
                consecutiveClassesRule="soft"
            )
        )
        
        # Time the schedule generation
        start_time = time.time()
        response = create_schedule_dev(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        convergence_times.append(duration_ms)
        
        # Verify schedule is valid
        assert_valid_schedule(response, request)
    
    print("\nSolver Convergence Times:")
    for classes, duration in zip(class_counts, convergence_times):
        print(f"{classes} classes: {duration}ms")
        
    # Check for reasonable scaling
    for i in range(1, len(convergence_times)):
        time_increase = convergence_times[i] / convergence_times[i-1]
        assert time_increase < 5, f"Solver scaling too steep between {class_counts[i-1]} and {class_counts[i]} classes"

def test_memory_scaling():
    """Test how memory usage scales with problem size"""
    class_counts = [5, 10, 15, 20, 25]
    memory_increases = []
    
    for num_classes in class_counts:
        request = ScheduleRequestGenerator.create_request(
            num_classes=num_classes,
            num_weeks=2,
            constraints=ScheduleConstraints(
                maxClassesPerDay=5,
                maxClassesPerWeek=15,
                minPeriodsPerWeek=1,
                maxConsecutiveClasses=2,
                consecutiveClassesRule="soft"
            )
        )
        
        # Measure memory usage
        start_memory = measure_memory_usage()
        response = create_schedule_dev(request)
        memory_increase = measure_memory_usage() - start_memory
        
        memory_increases.append(memory_increase)
        
        # Verify schedule is valid
        assert_valid_schedule(response, request)
    
    print("\nMemory Scaling:")
    for classes, memory in zip(class_counts, memory_increases):
        print(f"{classes} classes: {memory:.2f}MB")
        
    # Check for reasonable scaling
    for i in range(1, len(memory_increases)):
        memory_ratio = memory_increases[i] / memory_increases[i-1]
        assert memory_ratio < 3, f"Memory scaling too steep between {class_counts[i-1]} and {class_counts[i]} classes"
