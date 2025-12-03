"""Parallel execution with rate limiting and determinism"""

import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Optional, Dict
from dataclasses import dataclass
from queue import Queue
import time


@dataclass
class RateLimiter:
    """Rate limiter for adapter calls"""
    
    max_calls: int = 60  # Max calls per window
    window_seconds: int = 60  # Time window
    _calls: List[float] = None
    _lock: threading.Lock = None
    
    def __post_init__(self):
        if self._calls is None:
            self._calls = []
        if self._lock is None:
            self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """Try to acquire a rate limit slot. Returns True if allowed."""
        with self._lock:
            now = time.time()
            # Remove old calls outside the window
            self._calls = [t for t in self._calls if now - t < self.window_seconds]
            
            if len(self._calls) < self.max_calls:
                self._calls.append(now)
                return True
            return False
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded"""
        while not self.acquire():
            # Calculate wait time until oldest call expires
            with self._lock:
                if self._calls:
                    oldest = min(self._calls)
                    wait_time = self.window_seconds - (time.time() - oldest) + 0.1
                    if wait_time > 0:
                        time.sleep(min(wait_time, 1.0))
                    else:
                        # Clean up expired calls
                        now = time.time()
                        self._calls = [t for t in self._calls if now - t < self.window_seconds]


class ParallelExecutor:
    """Execute tasks in parallel with rate limiting and determinism"""
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        rate_limiter: Optional[RateLimiter] = None,
        seed: Optional[int] = None,
    ):
        """Initialize parallel executor.
        
        Args:
            max_workers: Maximum number of worker threads (default: min(32, CPU count + 4))
            rate_limiter: Optional rate limiter for adapter calls
            seed: Random seed for determinism
        """
        import os
        if max_workers is None:
            try:
                max_workers = min(32, (os.cpu_count() or 1) + 4)
            except:
                max_workers = 4
        
        self.max_workers = max_workers
        self.rate_limiter = rate_limiter
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
    
    def execute(
        self,
        tasks: List[Callable[[], Any]],
        sort_results: bool = True,
        preserve_order: bool = False,
    ) -> List[Any]:
        """Execute tasks in parallel.
        
        Args:
            tasks: List of callable tasks to execute
            sort_results: If True, sort results by task index (for determinism)
            preserve_order: If True, return results in same order as tasks
            
        Returns:
            List of results in order (if preserve_order) or sorted by index
        """
        if not tasks:
            return []
        
        # Create indexed tasks for sorting
        indexed_tasks = [(i, task) for i, task in enumerate(tasks)]
        
        # If seed is set, shuffle tasks but maintain determinism
        if self.seed is not None:
            rng = random.Random(self.seed)
            rng.shuffle(indexed_tasks)
        
        results: Dict[int, Any] = {}
        errors: Dict[int, Exception] = {}
        
        def execute_task(index: int, task: Callable[[], Any]) -> tuple[int, Any]:
            """Execute a single task with rate limiting"""
            if self.rate_limiter:
                self.rate_limiter.wait_if_needed()
            
            try:
                result = task()
                return (index, result)
            except Exception as e:
                return (index, e)
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(execute_task, idx, task): idx
                for idx, task in indexed_tasks
            }
            
            for future in as_completed(futures):
                idx, result = future.result()
                if isinstance(result, Exception):
                    errors[idx] = result
                else:
                    results[idx] = result
        
        # Collect results in order
        output = []
        for idx in range(len(tasks)):
            if idx in errors:
                raise errors[idx]
            if idx in results:
                output.append(results[idx])
            else:
                output.append(None)
        
        return output
    
    def execute_batches(
        self,
        tasks: List[Callable[[], Any]],
        batch_size: int = 10,
        sort_results: bool = True,
    ) -> List[Any]:
        """Execute tasks in batches to control memory usage.
        
        Args:
            tasks: List of callable tasks to execute
            batch_size: Number of tasks per batch
            sort_results: If True, sort results by task index
            
        Returns:
            List of results
        """
        all_results = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = self.execute(batch, sort_results=sort_results)
            all_results.extend(batch_results)
        
        return all_results


def get_adapter_rate_limiter(adapter_name: str) -> Optional[RateLimiter]:
    """Get rate limiter for a specific adapter based on its capabilities.
    
    Args:
        adapter_name: Name of the adapter
        
    Returns:
        RateLimiter instance or None if no limits needed
    """
    # Default rate limits (can be configured)
    limits = {
        "openai_compatible": RateLimiter(max_calls=60, window_seconds=60),
        "anthropic": RateLimiter(max_calls=50, window_seconds=60),
        "cohere": RateLimiter(max_calls=100, window_seconds=60),
        "mistral": RateLimiter(max_calls=50, window_seconds=60),
        "http_local": RateLimiter(max_calls=100, window_seconds=60),
        "hf_local": RateLimiter(max_calls=10, window_seconds=60),  # Local models are slower
    }
    
    return limits.get(adapter_name)

