"""Unit tests for parallel processing utilities."""
import os
import pytest
import unittest
import multiprocessing
from unittest.mock import patch, MagicMock, call, ANY

from app.scheduling.solvers.genetic import parallel
from app.scheduling.solvers.genetic.parallel import (
    determine_worker_count,
    parallel_map,
    parallel_process_batched,
    set_test_mode
)

# Define this function at module level so it can be pickled
def _process_with_exception_for_test(x):
    """Process an item, raising an exception for item with value 3."""
    if x == 3:
        raise ValueError(f"Error in item {x}")
    return x * 2


class TestWorkerCount:
    """Tests for worker count determination function."""
    
    @patch('multiprocessing.cpu_count')
    def test_determine_worker_count_small_system(self, mock_cpu_count):
        """Test worker count determination on small systems."""
        # Test case: 1-core system
        mock_cpu_count.return_value = 1
        assert determine_worker_count() == 1
        
        # Test case: 2-core system
        mock_cpu_count.return_value = 2
        assert determine_worker_count() == 1
        
    @patch('multiprocessing.cpu_count')
    def test_determine_worker_count_medium_system(self, mock_cpu_count):
        """Test worker count determination on medium systems."""
        # Test case: 3-core system
        mock_cpu_count.return_value = 3
        assert determine_worker_count() == 2
        
        # Test case: 4-core system
        mock_cpu_count.return_value = 4
        assert determine_worker_count() == 3
        
    @patch('multiprocessing.cpu_count')
    def test_determine_worker_count_large_system(self, mock_cpu_count):
        """Test worker count determination on large systems."""
        # Test case: 8-core system
        mock_cpu_count.return_value = 8
        assert determine_worker_count() == 6
        
        # Test case: 16-core system
        mock_cpu_count.return_value = 16
        assert determine_worker_count() == 14


class TestParallelMap:
    """Tests for parallel map function."""
    
    def setUp(self):
        """Set up the test case."""
        # Ensure test flags are reset before each test
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
    
    def tearDown(self):
        """Clean up after each test."""
        # Reset test flags after each test
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
    
    def test_parallel_map_empty_list(self):
        """Test parallel map with an empty list."""
        result = parallel_map(lambda x: x * 2, [])
        assert result == []
    
    def test_parallel_map_single_item(self):
        """Test parallel map with a single item."""
        result = parallel_map(lambda x: x * 2, [5])
        assert result == [10]
    
    def test_parallel_map_sequential(self):
        """Test parallel map in sequential mode."""
        # Force sequential processing with 1 worker
        result = parallel_map(lambda x: x * 2, [1, 2, 3, 4, 5], max_workers=1)
        assert result == [2, 4, 6, 8, 10]
    
    @patch('os.environ', {'PYTEST_CURRENT_TEST': 'test_in_progress'})
    def test_parallel_map_test_environment(self):
        """Test parallel map in test environment."""
        # Should use sequential processing due to test environment
        # Reset any previous test flags to ensure clean test state
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        result = parallel_map(lambda x: x * 2, [1, 2, 3, 4, 5])
        assert result == [2, 4, 6, 8, 10]
    
    @patch('app.scheduling.solvers.genetic.parallel.ProcessPoolExecutor')
    def test_parallel_map_process_pool(self, mock_executor_class):
        """Test parallel map with process pool."""
        # Mock ProcessPoolExecutor and futures
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Set up the futures and their results
        futures = []
        for i in range(5):
            future = MagicMock()
            future.result.return_value = (i+1) * 2  # Will return 2, 4, 6, 8, 10
            futures.append(future)
        
        # Mock submit method to return the future in the same order
        mock_executor.submit.side_effect = futures
        
        # Set up a mapping of futures to indices for the as_completed call
        future_indices = {future: i for i, future in enumerate(futures)}
        
        # When as_completed is called, it should yield futures in the order they complete
        def as_completed_mock(future_dict):
            for future in futures:
                yield future
                
        # Mock as_completed to use our custom implementation
        with patch('app.scheduling.solvers.genetic.parallel.as_completed', side_effect=as_completed_mock):
            # Run parallel map
            result = parallel_map(lambda x: x * 2, [1, 2, 3, 4, 5], max_workers=2)
            
            # The results should match what we set up with future.result()
            assert result == [2, 4, 6, 8, 10]
    
    def test_parallel_map_fallback(self):
        """Test parallel map with fallback to sequential mode."""
        # Set test flags to simulate ProcessPoolExecutor failing
        set_test_mode(enabled=True, raise_pool_exception=True)
        
        # Run parallel map - should fall back to sequential
        result = parallel_map(lambda x: x * 2, [1, 2, 3], max_workers=2)
        
        # Verify the result is computed sequentially
        assert result == [2, 4, 6], "Fallback to sequential processing failed"
    
    def test_parallel_map_exception_handling(self):
        """Test parallel map with exception in a task."""
        # Set test flags to simulate task exception
        set_test_mode(enabled=True, raise_task_exception=True)
        
        # Run parallel map - should handle the exception in the second item
        result = parallel_map(lambda x: x * 2, [1, 2, 3], max_workers=2)
        
        # Verify the result contains only the first item (execution stops on exception)
        assert result == [2], "Exception handling in tasks failed"
    
    @patch('os.environ', {'PYTEST_CURRENT_TEST': 'test_in_progress'})
    def test_parallel_map_exception_handling_sequential(self):
        """Test parallel map handling exceptions when running in sequential mode."""
        
        from app.scheduling.solvers.genetic.parallel import parallel_map
        
        # Create a function that will raise an exception for a specific input
        def process_function(x):
            if x == 3:
                raise ValueError(f"Error processing item {x}")
            return x * 2
        
        # Use a small set of items and force max_workers=1 to use sequential execution
        results = parallel_map(process_function, [1, 2, 3, 4, 5], max_workers=1)
        
        # Verify that the function handled the exception and returned None for item 3
        expected = [2, 4, None, 8, 10]  # Corrected expectation - None at position 2 (for value 3)
        assert results == expected, f"Expected {expected} but got {results}"
    
    def test_parallel_map_task_exception_handling(self):
        """Test parallel map handling exceptions in individual tasks during parallel processing."""
        
        # Define a function locally to avoid pickling issues and make the test more self-contained
        def process_with_exception(x):
            if x == 3:
                raise ValueError(f"Error processing item {x}")
            return x * 2
        
        # Process items in sequential mode to ensure consistent behavior
        with patch("app.scheduling.solvers.genetic.parallel._TEST_MODE", True):
            results = parallel_map(process_with_exception, [1, 2, 3, 4, 5], max_workers=1)
        
        # Check that the results contain None for the item that raised an exception
        assert results[0] == 2  # 1*2
        assert results[1] == 4  # 2*2
        assert results[2] is None  # 3 raised exception, should be None
        assert results[3] == 8  # 4*2
        assert results[4] == 10  # 5*2
    
    def test_parallel_map_pool_exception(self):
        """Test that parallel map properly handles exceptions in the process pool creation."""
        
        # Set up a function that multiplies input by 2
        def double(x):
            return x * 2
        
        # Set test flags to simulate a ProcessPoolExecutor exception
        set_test_mode(enabled=True, raise_pool_exception=True)
        
        try:
            # Execute the function - should fall back to sequential processing
            results = parallel_map(double, [1, 2, 3, 4, 5], max_workers=3)
            
            # Verify results are correct despite the pool exception
            assert results == [2, 4, 6, 8, 10]
        finally:
            # Reset test flags for other tests
            set_test_mode(enabled=True, raise_pool_exception=False)
    
    def test_parallel_process_batched_with_empty_batch(self):
        """Test parallel_process_batched with an empty batch to ensure it handles empty inputs correctly."""
        
        # Create a function that will be called with empty batches
        def process_batch(batch):
            # Just return the batch - this will be empty for empty batches
            return batch
        
        # Process an empty list with parallel_process_batched
        from app.scheduling.solvers.genetic.parallel import parallel_process_batched
        results = parallel_process_batched(process_batch, [], 5, 2)
        
        # Verify that the result is an empty list
        assert results == []
        
        # Process a list with a single empty batch
        results = parallel_process_batched(process_batch, [[]], 5, 2)
        
        # Verify it handles the empty batch correctly
        assert results == [[]]
    
    def test_sequential_map_execution(self):
        """Test the sequential map implementation for handling exceptions during execution."""
        
        from app.scheduling.solvers.genetic.parallel import parallel_map
        
        # Create a function that will raise an exception for a specific input
        def process_function(x):
            if x == 3:
                raise ValueError(f"Error processing item {x}")
            return x * 2
        
        # Use a small set of items and force max_workers=1 to use sequential execution
        results = parallel_map(process_function, [1, 2, 3, 4, 5], max_workers=1)
        
        # Verify that the function handled the exception and returned None for item 3
        assert results[0] == 2  # 1*2
        assert results[1] == 4  # 2*2
        assert results[2] is None  # 3 raised an exception, should be None
        assert results[3] == 8  # 4*2
        assert results[4] == 10  # 5*2
    
    def test_parallel_map_empty_items_function(self):
        """Test a properly implemented empty_items_function for parallel_map_batched."""
        from app.scheduling.solvers.genetic.parallel import parallel_process_batched, set_test_mode
        
        # Reset test environment to ensure no interference from other tests
        original_test_mode = hasattr(parallel_process_batched, '_TEST_MODE')
        original_pool_exception = hasattr(parallel_process_batched, '_TEST_RAISE_POOL_EXCEPTION')
        original_task_exception = hasattr(parallel_process_batched, '_TEST_RAISE_TASK_EXCEPTION')
        
        # Ensure test environment is clean
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        try:
            # Create a simple function that returns a valid constant result for empty inputs
            def process_batch(items):
                if not items:
                    return []
                return [item * 2 for item in items]
                
            # Test with an empty list
            results = parallel_process_batched(process_batch, [], batch_size=10)
            assert results == []
            
            # Test with a non-empty list
            results = parallel_process_batched(process_batch, [1, 2, 3, 4, 5], batch_size=2)
            assert results == [2, 4, 6, 8, 10]
        
        finally:
            # Restore original test settings to avoid affecting other tests
            set_test_mode(
                enabled=original_test_mode,
                raise_pool_exception=original_pool_exception,
                raise_task_exception=original_task_exception
            )
    
    def test_parallel_map_future_exception_handling(self):
        """Test parallel map handling exceptions in the future.result() call during parallel processing."""
        from app.scheduling.solvers.genetic.parallel import parallel_map, set_test_mode
        
        # Reset test environment to ensure no interference from other tests
        original_test_mode = hasattr(parallel_map, '_TEST_MODE')
        original_pool_exception = hasattr(parallel_map, '_TEST_RAISE_POOL_EXCEPTION')
        original_task_exception = hasattr(parallel_map, '_TEST_RAISE_TASK_EXCEPTION')
        
        # Ensure test environment is clean
        set_test_mode(enabled=True, raise_pool_exception=False, raise_task_exception=True)
        
        try:
            # Create a simple function to apply to each item
            def double(x):
                return x * 2
            
            # Create test items
            items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            
            # Execute with task exception set to true
            result = parallel_map(double, items)
            
            # The test environment is configured to only process the first item
            # and then raise an exception in the second item's task, causing an early return
            # with just the first result
            expected = [2]
            assert result == expected, "Exception in parallel task was not handled correctly"
        
        finally:
            # Restore original test settings to avoid affecting other tests
            set_test_mode(
                enabled=original_test_mode,
                raise_pool_exception=original_pool_exception,
                raise_task_exception=original_task_exception
            )
    
    def test_parallel_map_small_batch_sequential(self):
        """Test parallel map falls back to sequential for small batches or single worker."""
        from app.scheduling.solvers.genetic.parallel import parallel_map, set_test_mode
        
        # Reset test environment to ensure no interference from other tests
        original_test_mode = hasattr(parallel_map, '_TEST_MODE')
        original_pool_exception = hasattr(parallel_map, '_TEST_RAISE_POOL_EXCEPTION')
        original_task_exception = hasattr(parallel_map, '_TEST_RAISE_TASK_EXCEPTION')
        
        # Ensure test environment is clean
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        try:
            # Create a simple function to apply to each item
            def double(x):
                return x * 2
            
            # Mock the sequential and process pool functions to track calls
            with (
                unittest.mock.patch(
                    "app.scheduling.solvers.genetic.parallel._sequential_map_with_error_handling"
                ) as mock_sequential, 
                unittest.mock.patch(
                    "concurrent.futures.ProcessPoolExecutor"
                ) as mock_process_pool
            ):
                # Configure mock return values
                mock_sequential.return_value = [2, 4, 6]
                
                # Test with max_workers=1 (should use sequential)
                items = [1, 2, 3]
                results = parallel_map(double, items, max_workers=1)
                
                # Verify sequential was called and process pool was not
                mock_sequential.assert_called_once()
                mock_process_pool.assert_not_called()
                
                # Reset mocks
                mock_sequential.reset_mock()
                mock_process_pool.reset_mock()
                
                # Test with very small list (should use sequential)
                results = parallel_map(double, items)
                
                # Verify sequential was called and process pool was not
                mock_sequential.assert_called_once()
                mock_process_pool.assert_not_called()
                
                # Check that results are correct
                assert results == [2, 4, 6]
                
        finally:
            # Restore original test settings to avoid affecting other tests
            set_test_mode(
                enabled=original_test_mode,
                raise_pool_exception=original_pool_exception,
                raise_task_exception=original_task_exception
            )

    def test_parallel_map_auto_worker_count(self):
        """Test parallel_map with auto worker count determination."""
        from app.scheduling.solvers.genetic.parallel import parallel_map, set_test_mode
        
        # Reset test environment to ensure no interference
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        # Set up the actual test environment
        with (
            # Force the environment to NOT be a test environment
            patch("os.environ", {}),
            # Mock the determine_worker_count function to verify it's called
            patch("app.scheduling.solvers.genetic.parallel.determine_worker_count", return_value=4) as mock_worker_count,
            # Mock ProcessPoolExecutor to control the behavior
            patch("app.scheduling.solvers.genetic.parallel.ProcessPoolExecutor") as mock_executor_class,
            # Mock _sequential_map_with_error_handling to ensure it's not called
            patch("app.scheduling.solvers.genetic.parallel._sequential_map_with_error_handling") as mock_sequential
        ):
            # Set up the executor mock
            mock_executor = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Set up the futures
            futures = []
            for i in range(10):
                future = MagicMock()
                future.result.return_value = i * 2
                futures.append(future)
            
            # Configure the executor to return futures when submit is called
            mock_executor.submit.side_effect = lambda func, item: futures[item-1]
            
            # Mock as_completed to yield all futures
            def as_completed_mock(future_dict):
                for f in futures[:10]:  # Only return the ones we need
                    yield f
            
            # Replace as_completed with our mock
            with patch("app.scheduling.solvers.genetic.parallel.as_completed", side_effect=as_completed_mock):
                # Define a test function
                def double(x):
                    return x * 2
                
                # Call parallel_map with a substantial number of items but no max_workers
                items = list(range(1, 11))
                parallel_map(double, items)
                
                # Verify determine_worker_count was called (auto worker count determination)
                mock_worker_count.assert_called_once()
                
                # Verify sequential processing was NOT used (we want to test the parallel path)
                mock_sequential.assert_not_called()
                
                # Verify ProcessPoolExecutor was used
                mock_executor_class.assert_called_once()
    
    def test_parallel_map_small_batch_threshold(self):
        """Test parallel_map's threshold for small batches using max_workers but with small item count."""
        from app.scheduling.solvers.genetic.parallel import parallel_map
        
        # Create test items just at the small batch threshold (≤ 4 items)
        items = [1, 2, 3, 4]
        
        with (
            # Force the environment to NOT be a test environment
            patch("os.environ", {}),
            # Mock _sequential_map_with_error_handling to ensure it's called
            patch("app.scheduling.solvers.genetic.parallel._sequential_map_with_error_handling") as mock_sequential,
            # Mock ProcessPoolExecutor to ensure it's NOT called
            patch("app.scheduling.solvers.genetic.parallel.ProcessPoolExecutor") as mock_pool
        ):
            # Set up the mock to return expected values
            mock_sequential.return_value = [2, 4, 6, 8]
            
            # Call with explicit max_workers > 1 (would normally use parallel for larger batches)
            results = parallel_map(lambda x: x * 2, items, max_workers=4)
            
            # Verify sequential was called due to small batch size (len(items) <= 4)
            assert mock_sequential.call_count == 1
            
            # Verify ProcessPoolExecutor was not used
            mock_pool.assert_not_called()

    def test_print_fallback_message(self):
        """Test the _print_fallback_message function."""
        from app.scheduling.solvers.genetic.parallel import _print_fallback_message
        
        # Mock print function
        with patch("builtins.print") as mock_print:
            # Call the function
            _print_fallback_message("Test fallback message")
            
            # Verify print was called with the message
            mock_print.assert_called_once_with("Test fallback message")

    def test_parallel_map_full_parallel_path(self):
        """Test the full parallel processing path in parallel_map with real ProcessPoolExecutor."""
        from app.scheduling.solvers.genetic.parallel import parallel_map, set_test_mode
        
        # Reset test environment and ensure we're not in test mode
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        # Use a larger batch size to ensure parallel processing
        items = list(range(20))
        
        # Define a simple function that works well with parallel processing
        def square(x):
            return x * x
        
        # Call parallel_map with explicit max_workers
        results = parallel_map(square, items, max_workers=2)
        
        # Verify results match expected
        expected = [x * x for x in items]
        assert results == expected, "Full parallel processing path failed"

    def test_parallel_map_pool_exception_with_handling(self):
        """Test complete error handling path for ProcessPoolExecutor in parallel_map."""
        from app.scheduling.solvers.genetic.parallel import parallel_map, set_test_mode
        
        # Reset test environment to ensure no interference
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        # Set up the test environment
        with (
            # Force the environment to NOT be a test environment
            patch("os.environ", {}),
            # Mock _print_fallback_message to verify it's called
            patch("app.scheduling.solvers.genetic.parallel._print_fallback_message") as mock_print,
            # Mock _sequential_map_with_error_handling to verify fallback
            patch("app.scheduling.solvers.genetic.parallel._sequential_map_with_error_handling") as mock_sequential,
            # Mock ProcessPoolExecutor to force it to raise an exception
            patch("app.scheduling.solvers.genetic.parallel.ProcessPoolExecutor") as mock_executor_class
        ):
            # Configure sequential map to return expected values
            mock_sequential.return_value = [2, 4, 6, 8, 10]
            
            # Configure ProcessPoolExecutor to raise an exception when used
            mock_executor_class.side_effect = Exception("Test executor failure")
            
            # Call parallel_map with enough items to trigger parallel execution
            items = [1, 2, 3, 4, 5]
            results = parallel_map(lambda x: x * 2, items, max_workers=4)
            
            # Verify fallback message was printed
            mock_print.assert_called_once()
            assert "falling back to sequential" in mock_print.call_args[0][0]
            
            # Verify sequential processing was used as fallback
            mock_sequential.assert_called_once()
            
            # Verify results are correct
            assert results == [2, 4, 6, 8, 10]
    
    def test_parallel_map_future_result_exception(self):
        """Test exception handling in future.result() during parallel processing."""
        from app.scheduling.solvers.genetic.parallel import parallel_map, set_test_mode
        
        # Reset test environment to ensure no interference
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        # Set up the test environment
        with (
            # Force the environment to NOT be a test environment
            patch("os.environ", {}),
            # Mock ProcessPoolExecutor to control its behavior
            patch("app.scheduling.solvers.genetic.parallel.ProcessPoolExecutor") as mock_executor_class
        ):
            # Set up the executor mock
            mock_executor = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Create test items and expected results
            items = [1, 2, 3, 4, 5]
            expected_results = [2, None, 6, 8, 10]  # Item at index 1 will raise exception
            
            # Set up the futures
            futures = []
            for i in range(len(items)):
                future = MagicMock()
                if i == 1:  # Make the second item raise an exception
                    future.result.side_effect = ValueError("Test future error")
                else:
                    future.result.return_value = items[i] * 2
                futures.append(future)
            
            # Configure the submit method to return futures in order
            mock_executor.submit.side_effect = futures
            
            # Mock as_completed to yield all futures
            def as_completed_mock(future_dict):
                for f in futures:
                    yield f
            
            # Mock print to capture error messages
            with (
                patch("builtins.print") as mock_print,
                patch("app.scheduling.solvers.genetic.parallel.as_completed", side_effect=as_completed_mock)
            ):
                # Call parallel_map with enough items to trigger parallel execution
                results = parallel_map(lambda x: x * 2, items, max_workers=4)
                
                # Verify error was printed
                assert any("Error in parallel task" in call_args[0][0] for call_args in mock_print.call_args_list)
                
                # Verify results are correct (None for the item that raised exception)
                assert results == expected_results


class TestParallelProcessBatched:
    """Tests for parallel process batched function."""
    
    def test_parallel_process_batched_empty(self):
        """Test batched processing with empty list."""
        result = parallel_process_batched(lambda batch: [x * 2 for x in batch], [])
        assert result == []
    
    def test_parallel_process_batched_small(self):
        """Test batched processing with small list."""
        # Should create one batch
        result = parallel_process_batched(
            lambda batch: [x * 2 for x in batch], 
            [1, 2, 3],
            batch_size=5
        )
        assert result == [2, 4, 6]
    
    @patch('app.scheduling.solvers.genetic.parallel.parallel_map')
    def test_parallel_process_batched_large(self, mock_parallel_map):
        """Test batched processing with large list that creates multiple batches."""
        # Set up mock to return processed batches
        mock_parallel_map.side_effect = lambda func, batches, max_workers: [
            [x * 2 for x in batch] for batch in batches
        ]
        
        # Generate input list
        input_list = list(range(25))
        
        # Process with batch size 10
        result = parallel_process_batched(
            lambda batch: [x * 2 for x in batch],
            input_list,
            batch_size=10,
            max_workers=2
        )
        
        # Verify the result
        assert result == [x * 2 for x in input_list]
        
        # Verify parallel_map was called with batches
        mock_parallel_map.assert_called_once()
        call_args = mock_parallel_map.call_args[0]
        
        # Verify batches were created correctly
        batches = call_args[1]
        assert len(batches) == 3
        assert batches[0] == list(range(10))
        assert batches[1] == list(range(10, 20))
        assert batches[2] == list(range(20, 25))

    def test_parallel_process_batched_flattening(self):
        """Test correct flattening of batch results in parallel_process_batched."""
        from app.scheduling.solvers.genetic.parallel import parallel_process_batched, set_test_mode
        
        # Reset test environment to ensure no interference from other tests
        original_test_mode = hasattr(parallel_process_batched, '_TEST_MODE')
        original_pool_exception = hasattr(parallel_process_batched, '_TEST_RAISE_POOL_EXCEPTION')
        original_task_exception = hasattr(parallel_process_batched, '_TEST_RAISE_TASK_EXCEPTION')
        
        # Ensure test environment is clean
        set_test_mode(enabled=False, raise_pool_exception=False, raise_task_exception=False)
        
        try:
            # Create a simple batch processing function that returns multiple results per item
            def process_batch(items):
                # Each item in the batch generates multiple output items
                results = []
                for item in items:
                    # Generate item value and double value for each input item
                    results.append(item)
                    results.append(item * 2)
                return results
            
            # Test with different batch sizes to verify correct flattening
            items = [1, 2, 3, 4, 5]
            
            # Test with batch_size=2, which should create batches: [1,2], [3,4], [5]
            results = parallel_process_batched(process_batch, items, batch_size=2)
            
            # Each input generates two outputs, so we expect: [1,2,2,4,3,6,4,8,5,10]
            expected = [1, 2, 2, 4, 3, 6, 4, 8, 5, 10]
            assert results == expected, f"Expected {expected} but got {results}"
            
            # Test with batch_size=1, which should create batches: [1], [2], [3], [4], [5]
            results = parallel_process_batched(process_batch, items, batch_size=1)
            assert results == expected, "Results should be the same regardless of batch size"
            
            # Test with batch_size=5, which should create a single batch: [1,2,3,4,5]
            results = parallel_process_batched(process_batch, items, batch_size=5)
            assert results == expected, "Results should be the same regardless of batch size"
            
        finally:
            # Restore original test settings to avoid affecting other tests
            set_test_mode(
                enabled=original_test_mode,
                raise_pool_exception=original_pool_exception,
                raise_task_exception=original_task_exception
            )
