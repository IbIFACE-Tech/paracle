#!/usr/bin/env python
"""Test API workflow execution with AgentExecutor."""

import asyncio

import httpx


async def test_workflow_execution():
    """Test workflow execution via API."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. List available workflows
        print("📋 Listing available workflows...")
        response = await client.get(f"{base_url}/api/workflows")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, dict) and "workflows" in data:
                workflows = data["workflows"]
            elif isinstance(data, list):
                workflows = data
            else:
                workflows = []

            print(f"Found {len(workflows)} workflows")
            for wf in workflows[:3]:
                print(f"  - {wf['id']}: {wf['spec']['name']}")
        else:
            print(f"Error: {response.text}")
            return

        # 2. Execute hello_world workflow
        print("\n🚀 Executing hello_world workflow...")
        execute_request = {
            "workflow_id": "hello_world",
            "inputs": {"name": "API Test"},
            "async_execution": False,  # Synchronous for testing
        }

        response = await client.post(
            f"{base_url}/api/workflows/execute", json=execute_request
        )
        print(f"Status: {response.status_code}")

        if response.status_code in (200, 202):
            result = response.json()
            print(f"Execution ID: {result['execution_id']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")

            # 3. Get execution status
            execution_id = result["execution_id"]
            print("\n📊 Getting execution status...")

            response = await client.get(
                f"{base_url}/api/workflows/executions/{execution_id}"
            )
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                status = response.json()
                print(f"Execution Status: {status['status']}")
                print(f"Progress: {status['progress'] * 100:.0f}%")
                print(f"Completed Steps: {status['completed_steps']}")

                if status.get("result"):
                    print("\n✅ Workflow Outputs:")
                    for key, value in status["result"].items():
                        print(f"  {key}: {value}")
                elif status.get("error"):
                    print(f"\n❌ Error: {status['error']}")
            else:
                print(f"Error: {response.text}")
        else:
            print(f"Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_workflow_execution())
