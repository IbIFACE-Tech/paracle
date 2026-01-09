"""Test API endpoints for Plan Mode and Dry-Run Mode.

Quick validation script to test new API features.
"""

import asyncio

import httpx


async def test_api_endpoints():
    """Test plan and dry-run endpoints."""
    base_url = "http://localhost:8000"

    # Test 1: Plan endpoint
    print("=" * 60)
    print("Test 1: Workflow Plan Endpoint")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Create a simple test workflow first
            workflow_data = {
                "name": "test-workflow",
                "spec": {
                    "steps": [
                        {
                            "id": "step1",
                            "agent": "test-agent",
                            "prompt": "First step",
                        },
                        {
                            "id": "step2",
                            "agent": "test-agent",
                            "prompt": "Second step",
                            "depends_on": ["step1"],
                        },
                    ]
                }
            }

            # Create workflow
            create_response = await client.post(
                f"{base_url}/api/workflows",
                json=workflow_data,
            )

            if create_response.status_code == 200:
                workflow_id = create_response.json()["id"]
                print(f"✓ Created workflow: {workflow_id}")

                # Test plan endpoint
                plan_response = await client.post(
                    f"{base_url}/api/workflows/{workflow_id}/plan"
                )

                if plan_response.status_code == 200:
                    plan = plan_response.json()
                    print("✓ Got execution plan:")
                    print(f"  - Total steps: {plan['total_steps']}")
                    print(
                        f"  - Estimated cost: ${plan['estimated_cost_usd']:.4f}")
                    print(
                        f"  - Estimated time: {plan['estimated_time_seconds']}s")
                    print(
                        f"  - Execution groups: {len(plan['execution_groups'])}")
                else:
                    print(
                        f"✗ Plan endpoint failed: {plan_response.status_code}")
                    print(f"  {plan_response.text}")
            else:
                print(
                    f"✗ Failed to create workflow: {create_response.status_code}")

    except Exception as e:
        print(f"✗ Error testing plan endpoint: {e}")

    # Test 2: Dry-run execution
    print("\n" + "=" * 60)
    print("Test 2: Dry-Run Execution")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Execute with dry-run
            exec_response = await client.post(
                f"{base_url}/api/workflows/execute",
                json={
                    "workflow_id": workflow_id,
                    "inputs": {},
                    "async_execution": False,
                    "dry_run": True,
                    "mock_strategy": "fixed",
                },
            )

            if exec_response.status_code == 202:
                result = exec_response.json()
                print("✓ Dry-run execution completed:")
                print(f"  - Execution ID: {result['execution_id']}")
                print(f"  - Status: {result['status']}")
                print(f"  - Message: {result['message']}")
            else:
                print(f"✗ Dry-run failed: {exec_response.status_code}")
                print(f"  {exec_response.text}")

    except Exception as e:
        print(f"✗ Error testing dry-run: {e}")

    print("\n" + "=" * 60)
    print("API Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("Starting API endpoint tests...")
    print("Make sure the API server is running: paracle serve\n")

    asyncio.run(test_api_endpoints())
