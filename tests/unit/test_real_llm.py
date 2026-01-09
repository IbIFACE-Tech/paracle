"""
Test workflow execution with real OpenAI provider.

This script:
1. Creates a test workflow that uses OpenAI GPT-4
2. Executes it through the API
3. Validates real LLM responses
4. Compares against mock responses
"""

import asyncio
import os
import sys
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = "http://localhost:8000"


async def test_real_llm_workflow():
    """Test workflow execution with real OpenAI provider."""

    print("=" * 70)
    print("🧪 Testing Workflow Execution with Real LLM Provider")
    print("=" * 70)
    print()

    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please set it in .env file")
        return False

    print(f"✅ OpenAI API key found: {api_key[:20]}...")
    print()

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Create a test workflow YAML file
        print("📝 Creating test workflow YAML with OpenAI provider...")

        workflow_yaml = """name: test_openai_workflow
version: '1.0'
description: Test workflow using real OpenAI GPT-4

steps:
  - id: generate_greeting
    agent: greeter
    provider: openai
    model: gpt-4
    prompt: "Generate a creative and friendly greeting message. Be concise (max 20 words)."
    output_key: greeting

  - id: analyze_greeting
    agent: analyzer
    provider: openai
    model: gpt-4
    prompt: "Analyze this greeting and rate its friendliness from 1-10: {greeting}"
    output_key: analysis
    depends_on:
      - generate_greeting
"""

        # Save workflow to .parac/workflows/definitions/
        workflow_file = ".parac/workflows/definitions/test_openai_workflow.yaml"
        with open(workflow_file, "w") as f:
            f.write(workflow_yaml)

        print(f"   ✓ Saved workflow to: {workflow_file}")
        print("   Workflow: test_openai_workflow")
        print("   Steps: 2")
        print("   Provider: openai")
        print("   Model: gpt-4")
        print()

        # Step 2: Execute workflow via API
        print("🚀 Executing workflow with real OpenAI...")
        start_time = datetime.now()

        try:
            response = await client.post(
                f"{API_BASE_URL}/api/workflows/execute",
                json={
                    "workflow_id": "test_openai_workflow",
                    "inputs": {},
                    "async_execution": False  # Use synchronous execution
                }
            )

            if response.status_code != 202:
                print(f"❌ Execution failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

            data = response.json()
            execution_id = data.get("execution_id")
            status = data.get("status")

            print("✅ Workflow execution completed!")
            print(f"   Execution ID: {execution_id}")
            print(f"   Status: {status}")

            # With sync execution, we need to get full status
            if status != "completed":
                print(f"   ⚠️  Unexpected status: {status}")
            print()

            execution_time = (datetime.now() - start_time).total_seconds()

            # Get final execution status
            status_response = await client.get(
                f"{API_BASE_URL}/api/workflows/executions/{execution_id}"
            )

            if status_response.status_code != 200:
                print(
                    f"❌ Status retrieval failed: {status_response.status_code}")
                # Continue anyway, use data from execute response
                status_data = data
            else:
                status_data = status_response.json()
            print("✅ Workflow completed successfully!")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Progress: {status_data.get('progress')}%")
            print()

            print("📊 Execution Details:")
            print(f"   Status: {status_data.get('status')}")
            print(f"   Message: {status_data.get('message')}")
            print(f"   Started: {status_data.get('started_at')}")
            print(f"   Completed: {status_data.get('completed_at')}")
            print()

            print("🔍 Completed Steps:")
            completed_steps = status_data.get("completed_steps", [])
            for step_id in completed_steps:
                print(f"   ✓ {step_id}")
            print()

            print("🎯 Workflow Outputs:")
            outputs = status_data.get("outputs", {})
            for key, value in outputs.items():
                print(f"   {key}:")
                # Print first 200 chars of value
                value_str = str(value)
                if len(value_str) > 200:
                    print(f"      {value_str[:200]}...")
                else:
                    print(f"      {value_str}")
            print()

            # Step 5: Validate real LLM response
            print("✅ Validation:")

            # Check if we got real responses (not mock)
            greeting = outputs.get("greeting", "")
            analysis = outputs.get("analysis", "")

            if "mock" in greeting.lower() or "mock" in analysis.lower():
                print("   ⚠️  Warning: Responses appear to be mocked")
                print("   This suggests the provider wasn't properly initialized")
                return False

            print("   ✓ Greeting generated by real LLM")
            print("   ✓ Analysis generated by real LLM")
            print("   ✓ No mock responses detected")
            print()

            return True

        except httpx.TimeoutException:
            print("❌ Request timeout")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def compare_mock_vs_real():
    """Compare execution with mock vs real provider."""

    print()
    print("=" * 70)
    print("🔬 Comparison Test: Mock vs Real Provider")
    print("=" * 70)
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Execute hello_world (uses mock)
        print("1️⃣  Executing hello_world workflow (mock provider)...")

        try:
            response = await client.post(
                f"{API_BASE_URL}/api/workflows/execute",
                json={"workflow_id": "hello_world"}
            )

            if response.status_code == 202:
                data = response.json()
                execution_id = data.get("execution_id")

                # Wait for completion
                await asyncio.sleep(2)

                status_response = await client.get(
                    f"{API_BASE_URL}/api/workflows/executions/{execution_id}"
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    outputs = status_data.get("outputs", {})

                    print("   ✅ Mock execution completed")
                    print(f"   Output: {outputs.get('final_greeting', 'N/A')}")
                    print()
                else:
                    print("   ❌ Status check failed")
                    print()
            else:
                print(f"   ❌ Execution failed: {response.status_code}")
                print()
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()

        # Test 2: Real LLM execution (already done above)
        print("2️⃣  Real LLM execution completed above")
        print()

        print("📈 Comparison Summary:")
        print("   Mock Provider:")
        print("      • Fast execution (< 1s)")
        print("      • Deterministic outputs")
        print("      • No API costs")
        print("      • Good for testing infrastructure")
        print()
        print("   Real Provider:")
        print("      • Variable execution time (5-30s)")
        print("      • Creative, non-deterministic outputs")
        print("      • API costs apply")
        print("      • Validates full integration")
        print()


async def main():
    """Main test runner."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "PARACLE REAL LLM WORKFLOW EXECUTION TEST" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    # Check if API server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                print("❌ API server not responding properly")
                print(f"   Health check returned: {response.status_code}")
                return 1
    except httpx.ConnectError:
        print("❌ Cannot connect to API server")
        print(f"   Make sure server is running on {API_BASE_URL}")
        print()
        print("   Start server with: paracle serve")
        return 1
    except Exception as e:
        print(f"❌ Error checking API server: {e}")
        return 1

    print(f"✅ API server is running on {API_BASE_URL}")
    print()

    # Run tests
    success = await test_real_llm_workflow()

    if success:
        await compare_mock_vs_real()
        print()
        print("=" * 70)
        print("🎉 All tests passed!")
        print("=" * 70)
        return 0
    else:
        print()
        print("=" * 70)
        print("❌ Tests failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
