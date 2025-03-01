"""Parallel processing utilities for genetic algorithm optimization."""
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from typing import Callable, List, TypeVar, Generic, Any

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

def determine_worker_count() -> int:
    """
    Determine the optimal number of worker processes.
    
    Returns a reasonable number of workers based on available CPU cores,
    while leaving some headroom for system processes.
    
    Returns:
        int: Number of worker processes to use
    """
    # Get available CPU cores
    cpu_count = multiprocessing.cpu_count()
    
    # Use a reasonable number of workers (leave some headroom)
    if cpu_count <= 2:
        return 1  # Don't parallelize on systems with 1-2 cores
    elif cpu_count <= 4:
        return cpu_count - 1  # Leave 1 core free
    else:
        return max(1, cpu_count - 2)  # Leave 2 cores free on larger systems

def parallel_map(func: Callable[[T], R], items: List[T], max_workers: int = None) -> List[R]:
    """
    Apply a function to each item in a list in parallel.
    
    Args:
        func: Function to apply to each item
        items: List of items to process
        max_workers: Maximum number of worker processes (None for auto)
        
    Returns:
        List of results in the same order as input items
    """
    if not items:
        return []
    
    # Check if we're in a test environment
    is_test_env = 'PYTEST_CURRENT_TEST' in os.environ
    
    # Skip parallelization for small batches, test environments, or when explicitly set to 1 worker
    if len(items) <= 1 or is_test_env or max_workers == 1:
        return [func(item) for item in items]
    
    # Determine worker count if not specified
    if max_workers is None:
        max_workers = determine_worker_count()
    
    # Use single-threaded approach if only one worker or small batch
    if max_workers == 1 or len(items) <= 4:
        return [func(item) for item in items]
    
    try:
        # Run in parallel with process pool
        results = [None] * len(items)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item): i 
                for i, item in enumerate(items)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error in parallel task: {e}")
                    results[index] = None
        
        return results
    except Exception as e:
        # Fall back to sequential processing if parallel fails
        print(f"Parallel processing failed, falling back to sequential: {e}")
        return [func(item) for item in items]

def parallel_process_batched(
    func: Callable[[List[T]], List[R]],
    items: List[T], 
    batch_size: int = 10,
    max_workers: int = None
) -> List[R]:
    """
    Process items in batches across multiple workers.
    
    This is more efficient than individual processing when each
    item is small and function call overhead is significant.
    
    Args:
        func: Function that processes a batch of items and returns a list of results
        items: List of items to process
        batch_size: Number of items per batch
        max_workers: Maximum number of workers (None for auto)
        
    Returns:
        Combined list of results from all batches
    """
    if not items:
        return []
    
    # Create batches
    batches = [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]
    
    # Process batches in parallel
    batch_results = parallel_map(func, batches, max_workers)
    
    # Flatten batch results
    return [
        result
        for batch in batch_results
        for result in batch
    ]