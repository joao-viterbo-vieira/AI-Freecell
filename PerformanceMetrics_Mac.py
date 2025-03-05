import time
import psutil
import os
import platform


class PerformanceMetrics:
    def __init__(self):
        # Initialize peak memory tracking first
        self.process = psutil.Process(os.getpid())
        self.memory_snapshots = []
        self.reset()

    def reset(self):
        self.start_time = 0
        self.end_time = 0
        self.start_memory = 0
        self.end_memory = 0
        self.states_explored = 0
        self.states_generated = 0
        self.max_queue_size = 0
        self.solution_length = 0
        self.max_depth_reached = 0
        self.branching_factor = 0
        self.memory_used = 0
        self.max_memory = 0
        self.peak_memory = 0
        self.avg_memory = 0
        self.memory_snapshots = []

        # Take initial memory snapshot
        self.track_peak_memory()

    def track_peak_memory(self):
        """Update peak memory if current usage is higher and store snapshot"""
        current = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_snapshots.append(current)
        if current > self.peak_memory:
            self.peak_memory = current

    def sample_memory(self):
        """Take a memory snapshot for average calculation without affecting peak tracking"""
        current = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_snapshots.append(current)

    def start(self):
        self.start_time = time.time()
        # Force garbage collection before measuring starting memory
        import gc

        gc.collect()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory  # Reset peak memory tracking

    def stop(self, solution=None):
        self.end_time = time.time()
        self.track_peak_memory()  # One final check

        # Wait a moment for memory operations to complete
        time.sleep(0.1)
        # Force garbage collection before measuring final memory
        import gc

        gc.collect()

        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        if solution:
            self.solution_length = len(solution)

    def print_report(self, algorithm_name):
        elapsed_time = self.end_time - self.start_time

        # Calculate memory difference
        memory_diff = self.end_memory - self.start_memory

        # If memory difference is very small, it's likely measurement noise
        if abs(memory_diff) < 0.1:  # Less than 0.1 MB difference
            # Use peak memory minus start memory instead
            self.memory_used = self.peak_memory - self.start_memory
        else:
            self.memory_used = max(
                0.01, memory_diff
            )  # Ensure at least minimal positive value

        # Calculate average memory usage from snapshots
        if self.memory_snapshots:
            self.avg_memory = sum(self.memory_snapshots) / len(self.memory_snapshots)

        print("\n" + "=" * 50)
        print(f"PERFORMANCE REPORT - {algorithm_name}")
        print("=" * 50)
        print(f"Time used: {elapsed_time:.4f} seconds")
        print(f"Memory used: {self.memory_used:.2f} MB")
        print(f"Average memory: {self.avg_memory:.2f} MB")
        print(f"States explored: {self.states_explored}")
        print(f"States generated: {self.states_generated}")
        if elapsed_time > 0:
            print(f"States per second: {self.states_explored / elapsed_time:.2f}")
        print(f"Maximum queue size: {self.max_queue_size}")
        print(f"Solution length: {self.solution_length} moves")
        print(f"Maximum depth reached: {self.max_depth_reached}")

        # Get peak memory usage
        # Try to use platform-specific methods first
        system = platform.system()
        if system == "Windows":
            try:
                # Windows-specific peak working set size
                mem_info = self.process.memory_info()
                if hasattr(mem_info, "peak_wset"):
                    self.max_memory = mem_info.peak_wset / 1024 / 1024  # MB
                else:
                    self.max_memory = self.peak_memory
            except:
                self.max_memory = self.peak_memory
        else:
            # For macOS, Linux and others, use our tracked peak value
            self.max_memory = self.peak_memory

        print(f"Peak memory usage: {self.max_memory:.2f} MB")
        print("=" * 50)
