"""
Locust Performance Test Suite for Paracle API
Test Scenario 3: Mixed Load - Realistic Production Simulation

Purpose: Simulate realistic production traffic with mixed operations
Target: 500-1000 req/s with 1000+ concurrent users
SLA: p50<200ms, p95<500ms, p99<1s, error<0.1%
"""

import random

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner, WorkerRunner

# Configuration
API_BASE_URL = "http://localhost:8000"  # Override with --host flag
API_KEY = "test-api-key"  # Should be in environment variable


class MixedLoadUser(HttpUser):
    """
    Simulates realistic production user with mixed operations.

    Task weights represent realistic production traffic distribution:
    - 40% lightweight operations (list, get)
    - 30% medium operations (agent details, status checks)
    - 20% heavy operations (agent execution)
    - 8% very heavy operations (workflow execution)
    - 2% administrative operations
    """

    wait_time = between(1, 5)  # Realistic user think time

    def on_start(self):
        """Initialize user session."""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        }
        self.agent_ids = ["coder", "architect", "reviewer", "tester", "documenter"]
        self.workflow_ids = ["feature_development", "code_review", "bugfix"]

    @task(40)
    def list_agents(self):
        """List available agents - Lightweight operation."""
        with self.client.get(
            "/api/v1/agents",
            headers=self.headers,
            catch_response=True,
            name="API - List Agents",
        ) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure(
                    f"Response too slow: {response.elapsed.total_seconds():.2f}s"
                )
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(30)
    def get_agent_details(self):
        """Get agent details - Medium operation."""
        agent_id = random.choice(self.agent_ids)
        with self.client.get(
            f"/api/v1/agents/{agent_id}",
            headers=self.headers,
            catch_response=True,
            name="API - Get Agent Details",
        ) as response:
            if response.elapsed.total_seconds() > 1.0:
                response.failure(
                    f"Response too slow: {response.elapsed.total_seconds():.2f}s"
                )
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(20)
    def execute_quick_agent(self):
        """Execute quick agent task - Heavy operation."""
        agent_id = random.choice(self.agent_ids)
        tasks = [
            "Explain what a decorator is in Python",
            "Write a function to calculate factorial",
            "Create a simple REST API endpoint",
            "Explain list comprehension with example",
        ]

        payload = {
            "agent_id": agent_id,
            "task": random.choice(tasks),
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
        }

        with self.client.post(
            "/api/v1/agents/run",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="Agent - Quick Task",
        ) as response:
            if response.elapsed.total_seconds() > 5.0:
                response.failure(
                    f"Response too slow: {response.elapsed.total_seconds():.2f}s"
                )
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(8)
    def execute_workflow(self):
        """Execute workflow - Very heavy operation."""
        workflow_id = random.choice(self.workflow_ids)

        payloads = {
            "feature_development": {
                "workflow_id": "feature_development",
                "inputs": {
                    "feature_description": "Add JWT authentication to API",
                    "priority": "high",
                },
            },
            "code_review": {
                "workflow_id": "code_review",
                "inputs": {
                    "pr_url": "https://github.com/test/repo/pull/123",
                    "focus_areas": ["security", "performance"],
                },
            },
            "bugfix": {
                "workflow_id": "bugfix",
                "inputs": {
                    "bug_description": "API returns 500 on /agents endpoint",
                    "severity": "high",
                },
            },
        }

        payload = payloads[workflow_id]

        with self.client.post(
            "/api/v1/workflows/run",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name=f"Workflow - {workflow_id}",
        ) as response:
            if response.elapsed.total_seconds() > 30.0:
                response.failure(
                    f"Workflow too slow: {response.elapsed.total_seconds():.2f}s"
                )
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def check_health(self):
        """Health check - Administrative operation."""
        with self.client.get(
            "/health",
            headers=self.headers,
            catch_response=True,
            name="System - Health Check",
        ) as response:
            if response.elapsed.total_seconds() > 0.2:
                response.failure(
                    f"Health check too slow: {response.elapsed.total_seconds():.2f}s"
                )
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# Event handlers for distributed testing
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize test environment."""
    if isinstance(environment.runner, MasterRunner):
        print("🎯 Locust Master initialized")
        print(f"   Target: {environment.host}")
    elif isinstance(environment.runner, WorkerRunner):
        print(
            f"🔧 Locust Worker initialized (Master: {environment.runner.master_host})"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    if isinstance(environment.runner, MasterRunner):
        print("🚀 Starting Mixed Load Test")
        print(f"   Host: {environment.host}")
        print(f"   Users: {environment.runner.target_user_count}")
        print(f"   Spawn rate: {environment.runner.spawn_rate}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test completion and summary."""
    if isinstance(environment.runner, MasterRunner):
        stats = environment.stats
        print("\n📊 Test Results Summary:")
        print(f"   Total requests: {stats.total.num_requests}")
        print(f"   Total failures: {stats.total.num_failures}")
        print(f"   Average RPS: {stats.total.total_rps:.2f}")
        print(f"   p50 latency: {stats.total.get_response_time_percentile(0.50):.0f}ms")
        print(f"   p95 latency: {stats.total.get_response_time_percentile(0.95):.0f}ms")
        print(f"   p99 latency: {stats.total.get_response_time_percentile(0.99):.0f}ms")

        # Check SLA compliance
        p50 = stats.total.get_response_time_percentile(0.50)
        p95 = stats.total.get_response_time_percentile(0.95)
        p99 = stats.total.get_response_time_percentile(0.99)
        error_rate = (
            (stats.total.num_failures / stats.total.num_requests * 100)
            if stats.total.num_requests > 0
            else 0
        )

        print("\n✅ SLA Compliance Check:")
        print(f"   p50 < 200ms: {'✅ PASS' if p50 < 200 else '❌ FAIL'} ({p50:.0f}ms)")
        print(f"   p95 < 500ms: {'✅ PASS' if p95 < 500 else '❌ FAIL'} ({p95:.0f}ms)")
        print(
            f"   p99 < 1000ms: {'✅ PASS' if p99 < 1000 else '❌ FAIL'} ({p99:.0f}ms)"
        )
        print(
            f"   Error rate < 0.1%: {'✅ PASS' if error_rate < 0.1 else '❌ FAIL'} ({error_rate:.4f}%)"
        )


if __name__ == "__main__":
    # For standalone testing
    import os

    os.system("locust -f locustfile.py --host http://localhost:8000")
