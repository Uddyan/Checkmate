"""Tests for parallel execution"""

import pytest
import time
from checkmate.execution.parallel import ParallelExecutor, RateLimiter


def test_rate_limiter():
    """Test rate limiter"""
    limiter = RateLimiter(max_calls=5, window_seconds=1)
    
    # Should allow 5 calls
    for i in range(5):
        assert limiter.acquire() is True
    
    # 6th call should be blocked
    assert limiter.acquire() is False


def test_parallel_executor_basic():
    """Test basic parallel execution"""
    def task(x):
        return x * 2
    
    tasks = [lambda x=i: task(x) for i in range(10)]
    executor = ParallelExecutor(max_workers=4, seed=42)
    
    results = executor.execute(tasks, preserve_order=True)
    
    assert len(results) == 10
    assert results[0] == 0
    assert results[5] == 10
    assert results[9] == 18


def test_parallel_executor_determinism():
    """Test that parallel execution is deterministic with seed"""
    def task(x):
        return x
    
    tasks = [lambda x=i: task(x) for i in range(20)]
    
    executor1 = ParallelExecutor(max_workers=4, seed=42)
    results1 = executor1.execute(tasks, preserve_order=True)
    
    executor2 = ParallelExecutor(max_workers=4, seed=42)
    results2 = executor2.execute(tasks, preserve_order=True)
    
    # Results should be identical with same seed
    assert results1 == results2


def test_parallel_executor_with_rate_limiter():
    """Test parallel execution with rate limiting"""
    def task(x):
        time.sleep(0.01)  # Small delay
        return x
    
    limiter = RateLimiter(max_calls=5, window_seconds=1)
    tasks = [lambda x=i: task(x) for i in range(10)]
    
    executor = ParallelExecutor(max_workers=4, rate_limiter=limiter, seed=42)
    
    start = time.time()
    results = executor.execute(tasks, preserve_order=True)
    elapsed = time.time() - start
    
    # Should have rate limited (taken longer than without)
    assert len(results) == 10
    # Rate limiting should add some delay
    assert elapsed > 0.1


def test_parallel_executor_error_handling():
    """Test error handling in parallel execution"""
    def task(x):
        if x == 5:
            raise ValueError("Test error")
        return x
    
    tasks = [lambda x=i: task(x) for i in range(10)]
    executor = ParallelExecutor(max_workers=4, seed=42)
    
    with pytest.raises(ValueError, match="Test error"):
        executor.execute(tasks)

