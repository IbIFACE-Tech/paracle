"""Example: Using Paracle's built-in HTTP tools.

This example demonstrates how to use the HTTP tools:
- http_get: Make GET requests
- http_post: Make POST requests
- http_put: Make PUT requests
- http_delete: Make DELETE requests

Run: uv run python examples/02_http_tools.py

Note: Requires httpx to be installed (uv add httpx)
"""

import asyncio
import json

from paracle_tools import http_get, http_post, http_put, http_delete


async def main():
    """Demonstrate HTTP tool usage."""
    print("=" * 60)
    print("Paracle HTTP Tools Example")
    print("=" * 60)

    # =========================================================================
    # 1. HTTP GET - Fetch JSON data
    # =========================================================================
    print("\n1. GET request - Fetch user data from API...")

    result = await http_get.execute(
        url="https://jsonplaceholder.typicode.com/users/1"
    )

    if result.success:
        print(f"✓ Status: {result.output['status_code']}")
        print(f"  URL: {result.output['url']}")

        if result.output['json']:
            user = result.output['json']
            print(f"  User: {user['name']}")
            print(f"  Email: {user['email']}")
            print(f"  City: {user['address']['city']}")
    else:
        print(f"✗ Error: {result.error}")

    # =========================================================================
    # 2. HTTP GET - With query parameters and headers
    # =========================================================================
    print("\n2. GET request with parameters...")

    result = await http_get.execute(
        url="https://jsonplaceholder.typicode.com/posts",
        params={"userId": 1, "_limit": 3},
        headers={"Accept": "application/json"}
    )

    if result.success:
        print(f"✓ Status: {result.output['status_code']}")
        if result.output['json']:
            posts = result.output['json']
            print(f"  Found {len(posts)} posts")
            for post in posts:
                print(f"    - {post['title'][:50]}...")

    # =========================================================================
    # 3. HTTP POST - Create resource
    # =========================================================================
    print("\n3. POST request - Create new post...")

    new_post = {
        "title": "My Paracle Example",
        "body": "This post was created using Paracle's built-in HTTP tools!",
        "userId": 1
    }

    result = await http_post.execute(
        url="https://jsonplaceholder.typicode.com/posts",
        json_data=new_post
    )

    if result.success:
        print(f"✓ Status: {result.output['status_code']}")
        if result.output['json']:
            created = result.output['json']
            print(f"  Created post ID: {created.get('id')}")
            print(f"  Title: {created.get('title')}")

    # =========================================================================
    # 4. HTTP POST - Form data
    # =========================================================================
    print("\n4. POST request with form data...")

    result = await http_post.execute(
        url="https://httpbin.org/post",
        form_data={"field1": "value1", "field2": "value2"}
    )

    if result.success:
        print(f"✓ Status: {result.output['status_code']}")
        if result.output['json']:
            form_echo = result.output['json'].get('form', {})
            print(f"  Form data echoed: {form_echo}")

    # =========================================================================
    # 5. HTTP PUT - Update resource
    # =========================================================================
    print("\n5. PUT request - Update post...")

    updated_post = {
        "id": 1,
        "title": "Updated Title",
        "body": "Updated content",
        "userId": 1
    }

    result = await http_put.execute(
        url="https://jsonplaceholder.typicode.com/posts/1",
        json_data=updated_post
    )

    if result.success:
        print(f"✓ Status: {result.output['status_code']}")
        if result.output['json']:
            updated = result.output['json']
            print(f"  Updated title: {updated.get('title')}")

    # =========================================================================
    # 6. HTTP DELETE - Delete resource
    # =========================================================================
    print("\n6. DELETE request - Delete post...")

    result = await http_delete.execute(
        url="https://jsonplaceholder.typicode.com/posts/1"
    )

    if result.success:
        print(f"✓ Status: {result.output['status_code']}")
        print("  Resource deleted (simulated)")

    # =========================================================================
    # 7. CUSTOM TIMEOUT
    # =========================================================================
    print("\n7. Custom timeout configuration...")

    from paracle_tools.builtin.http import HTTPGetTool

    # Create tool with 5-second timeout
    fast_http = HTTPGetTool(timeout=5.0)

    result = await fast_http.execute(
        url="https://jsonplaceholder.typicode.com/users/1"
    )

    if result.success:
        print(f"✓ Request completed within timeout")
        print(f"  Status: {result.output['status_code']}")

    # =========================================================================
    # 8. ERROR HANDLING
    # =========================================================================
    print("\n8. Error handling examples...")

    # Invalid URL
    result = await http_get.execute(url="https://invalid-domain-that-does-not-exist-12345.com")
    print(f"Invalid domain: success={result.success}")
    if not result.success:
        print(f"  Error: {result.error[:100]}...")

    # 404 Not Found (still succeeds, but status code is 404)
    result = await http_get.execute(
        url="https://jsonplaceholder.typicode.com/posts/99999"
    )
    if result.success:
        print(f"Not found request: status={result.output['status_code']}")

    # =========================================================================
    # 9. REAL-WORLD EXAMPLE: GitHub API
    # =========================================================================
    print("\n9. Real-world example - GitHub API...")

    result = await http_get.execute(
        url="https://api.github.com/repos/python/cpython",
        headers={"Accept": "application/vnd.github.v3+json"}
    )

    if result.success and result.output['json']:
        repo = result.output['json']
        print(f"✓ Repository: {repo['full_name']}")
        print(f"  Description: {repo['description']}")
        print(f"  Stars: {repo['stargazers_count']:,}")
        print(f"  Forks: {repo['forks_count']:,}")
        print(f"  Language: {repo['language']}")

    # =========================================================================
    # 10. USING THE REGISTRY
    # =========================================================================
    print("\n10. Using BuiltinToolRegistry...")

    from paracle_tools import BuiltinToolRegistry

    # Create registry with custom timeout
    registry = BuiltinToolRegistry(http_timeout=10.0)

    # Execute tool through registry
    result = await registry.execute_tool(
        "http_get",
        url="https://jsonplaceholder.typicode.com/users/2"
    )

    if result.success and result.output['json']:
        user = result.output['json']
        print(f"✓ Via registry - User: {user['name']}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nNote: All HTTP requests in this example use public test APIs.")
    print("For production use, replace with your own API endpoints.")


if __name__ == "__main__":
    asyncio.run(main())
