import time
import psutil
import os


class PerformanceMetrics:
    def __init__(self):
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

    def start(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def stop(self, solution=None):
        self.end_time = time.time()
        self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        if solution:
            self.solution_length = len(solution)

    def print_report(self, algorithm_name):
        elapsed_time = self.end_time - self.start_time
        memory_used = self.end_memory - self.start_memory

        print("\n" + "=" * 50)
        print(f"PERFORMANCE REPORT - {algorithm_name}")
        print("=" * 50)
        print(f"Time used: {elapsed_time:.4f} seconds")
        print(f"Memory used: {memory_used:.2f} MB")
        print(f"States explored: {self.states_explored}")
        print(f"States generated: {self.states_generated}")
        if elapsed_time > 0:
            print(f"States per second: {self.states_explored / elapsed_time:.2f}")
        print(f"Maximum queue size: {self.max_queue_size}")
        print(f"Solution length: {self.solution_length} moves")
        print(f"Maximum depth reached: {self.max_depth_reached}")

        if self.states_explored > 0 and self.max_depth_reached > 0:
            # Effective branching factor calculation (approximation)
            ebf = self.states_generated ** (1 / max(1, self.max_depth_reached))
            print(f"Effective branching factor: {ebf:.2f}")

        # CPU and system resources
        cpu_percent = psutil.Process().cpu_percent()
        print(f"CPU usage: {cpu_percent:.1f}%")

        # Get peak memory usage with resource module
        if hasattr(psutil.Process(), "memory_info"):
            max_memory = psutil.Process(os.getpid()).memory_info().peak_wset / 1024 / 1024  # MB
        else:
            max_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        print(f"Peak memory usage: {max_memory:.2f} MB")
        print("=" * 50)
