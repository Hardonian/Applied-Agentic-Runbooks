"""
Benchmark and stress test execution engine integrated with runtime.
"""

import time
from typing import Any

from agent_factory.eval.model import BenchmarkSuite, EvaluationResult, Scenario
from agent_factory.runtime.engine import RuntimeEngine


class BenchmarkRunner:
    """Run benchmarks and stress tests using runtime engine."""
    
    def __init__(self, runtime: RuntimeEngine | None = None):
        """
        Initialize benchmark runner.
        
        Args:
            runtime: Runtime engine (optional, will create default if not provided)
        """
        self.runtime = runtime or RuntimeEngine()
    
    def run_benchmark(
        self,
        agent_id: str,
        suite: BenchmarkSuite,
    ) -> list[EvaluationResult]:
        """
        Run benchmark suite against an agent.
        
        Args:
            agent_id: Agent ID to test
            suite: Benchmark suite
        
        Returns:
            List of evaluation results
        """
        results = []
        
        for scenario in suite.scenarios:
            result = self._run_scenario(agent_id, scenario)
            results.append(result)
        
        return results
    
    def _run_scenario(self, agent_id: str, scenario: Scenario) -> EvaluationResult:
        """Run a single scenario."""
        start_time = time.time()
        
        try:
            # Run agent via runtime
            input_text = str(scenario.inputs.get("input", scenario.inputs))
            execution_id = self.runtime.run_agent(agent_id, input_text)
            execution = self.runtime.get_execution(execution_id)
            
            if not execution or execution.status != "completed":
                return EvaluationResult(
                    scenario_id=scenario.id,
                    agent_id=agent_id,
                    success=False,
                    error=execution.error if execution else "Execution failed",
                    latency=time.time() - start_time,
                )
            
            result = execution.result
            output = getattr(result, "output", str(result)) if result is not None else ""
            
            latency = time.time() - start_time
            
            # Calculate accuracy if expected outputs provided
            accuracy = None
            if scenario.expected_outputs:
                accuracy = self._calculate_accuracy(
                    {"output": output},
                    scenario.expected_outputs,
                )
            
            return EvaluationResult(
                scenario_id=scenario.id,
                agent_id=agent_id,
                success=True,
                accuracy=accuracy,
                latency=latency,
                tokens_used=getattr(result, "tokens_used", 0) if result is not None else 0,
                cost_estimate=0.0,
                output={"output": output},
            )
        except Exception as e:
            return EvaluationResult(
                scenario_id=scenario.id,
                agent_id=agent_id,
                success=False,
                error=str(e),
                latency=time.time() - start_time,
            )
    
    def _calculate_accuracy(self, output: dict[str, Any], expected: dict[str, Any]) -> float:
        """Calculate accuracy score."""
        if output == expected:
            return 1.0
        
        matches = 0
        total = len(expected)
        
        for key, expected_value in expected.items():
            if key in output and output[key] == expected_value:
                matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def stress_test(
        self,
        agent_id: str,
        concurrent_requests: int = 10,
        duration: int = 60,
    ) -> dict[str, Any]:
        """
        Run stress test (load testing).
        
        Args:
            agent_id: Agent ID to test
            concurrent_requests: Number of concurrent requests
            duration: Test duration in seconds
        
        Returns:
            Stress test results
        """
        import threading
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies": [],
        }
        
        stop_event = threading.Event()
        
        def make_request():
            """Make a single request."""
            start = time.time()
            try:
                execution_id = self.runtime.run_agent(agent_id, "test")
                execution = self.runtime.get_execution(execution_id)
                latency = time.time() - start
                
                results["total_requests"] += 1
                if execution and execution.status == "completed":
                    results["successful_requests"] += 1
                else:
                    results["failed_requests"] += 1
                results["latencies"].append(latency)
            except Exception:
                results["total_requests"] += 1
                results["failed_requests"] += 1
                results["latencies"].append(time.time() - start)
        
        def worker():
            """Worker thread."""
            while not stop_event.is_set():
                make_request()
                time.sleep(0.1)  # Small delay between requests
        
        # Start workers
        threads = []
        for _ in range(concurrent_requests):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        
        # Run for duration
        time.sleep(duration)
        stop_event.set()
        
        # Wait for threads
        for t in threads:
            t.join(timeout=1)
        
        # Calculate statistics
        raw_latencies = results.get("latencies", [])
        latencies: list[float] = [float(x) for x in raw_latencies] if isinstance(raw_latencies, list) else []
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p99_index = int(len(sorted_latencies) * 0.99)
        
        return {
            "agent_id": agent_id,
            "concurrent_requests": concurrent_requests,
            "duration": duration,
            "total_requests": results["total_requests"],
            "successful_requests": results["successful_requests"],
            "failed_requests": results["failed_requests"],
            "avg_latency": avg_latency,
            "p95_latency": sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else 0.0,
            "p99_latency": sorted_latencies[p99_index] if p99_index < len(sorted_latencies) else 0.0,
        }
