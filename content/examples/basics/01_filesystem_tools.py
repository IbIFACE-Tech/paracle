"""Example: Using Paracle's built-in filesystem tools.

This example demonstrates how to use the filesystem tools:
- read_file: Read file contents
- write_file: Write content to files
- list_directory: List directory contents
- delete_file: Delete files

Run: uv run python examples/01_filesystem_tools.py
"""

import asyncio
from pathlib import Path

from paracle_tools import read_file, write_file, list_directory, delete_file


async def main():
    """Demonstrate filesystem tool usage."""
    print("=" * 60)
    print("Paracle Filesystem Tools Example")
    print("=" * 60)

    # Create a temporary directory for this example
    example_dir = Path("./temp_example")
    example_dir.mkdir(exist_ok=True)

    # =========================================================================
    # 1. WRITE FILE
    # =========================================================================
    print("\n1. Writing files...")

    # Write a simple text file
    result = await write_file.execute(
        path=str(example_dir / "hello.txt"),
        content="Hello, Paracle!\nThis is a test file.",
    )

    if result.success:
        print(f"✓ Created file: {result.output['path']}")
        print(f"  Size: {result.output['size']} bytes")
        print(f"  Lines: {result.output['lines']}")
    else:
        print(f"✗ Error: {result.error}")

    # Write a config file
    config_content = """# Paracle Configuration
name: example-agent
model: gpt-4
temperature: 0.7
tools:
  - read_file
  - write_file
"""

    result = await write_file.execute(
        path=str(example_dir / "config.yaml"), content=config_content
    )

    if result.success:
        print(f"✓ Created config: {result.output['path']}")

    # Write to nested directory (auto-create parents)
    result = await write_file.execute(
        path=str(example_dir / "data" / "output.json"),
        content='{"status": "success", "count": 42}',
        create_dirs=True,
    )

    if result.success:
        print(f"✓ Created nested file: {result.output['path']}")

    # =========================================================================
    # 2. LIST DIRECTORY
    # =========================================================================
    print("\n2. Listing directory contents...")

    result = await list_directory.execute(path=str(example_dir))

    if result.success:
        print(f"✓ Found {result.output['count']} items in {result.output['path']}")
        for entry in result.output["entries"]:
            icon = "📁" if entry["type"] == "directory" else "📄"
            size = f"({entry.get('size', 0)} bytes)" if entry["type"] == "file" else ""
            print(f"  {icon} {entry['name']} {size}")

    # List recursively
    print("\n3. Listing recursively...")

    result = await list_directory.execute(path=str(example_dir), recursive=True)

    if result.success:
        print(f"✓ Found {result.output['count']} total items (recursive)")

    # =========================================================================
    # 4. READ FILE
    # =========================================================================
    print("\n4. Reading files...")

    result = await read_file.execute(path=str(example_dir / "hello.txt"))

    if result.success:
        print(f"✓ Read file: {result.output['path']}")
        print(f"  Content:\n{result.output['content']}")
        print(f"  Size: {result.output['size']} bytes")
        print(f"  Lines: {result.output['lines']}")

    # Read config file
    result = await read_file.execute(path=str(example_dir / "config.yaml"))

    if result.success:
        print(f"\n✓ Read config file:")
        print(result.output["content"])

    # =========================================================================
    # 5. PATH RESTRICTIONS (Security)
    # =========================================================================
    print("\n5. Demonstrating path restrictions...")

    # Create restricted tool that only allows access to example_dir
    from paracle_tools.builtin.filesystem import ReadFileTool

    restricted_reader = ReadFileTool(allowed_paths=[str(example_dir)])

    # This will succeed (within allowed path)
    result = await restricted_reader.execute(path=str(example_dir / "hello.txt"))
    print(f"✓ Allowed path access: {result.success}")

    # This will fail (outside allowed path)
    result = await restricted_reader.execute(path="/etc/passwd")
    print(f"✗ Restricted path access: {result.success}")
    if not result.success:
        print(f"  Error: {result.error}")

    # =========================================================================
    # 6. DELETE FILE
    # =========================================================================
    print("\n6. Cleaning up...")

    # Delete individual file
    result = await delete_file.execute(path=str(example_dir / "hello.txt"))

    if result.success:
        print(f"✓ Deleted: {result.output['path']}")

    # List remaining files
    result = await list_directory.execute(path=str(example_dir))
    if result.success:
        print(f"  Remaining files: {result.output['count']}")

    # Clean up example directory
    import shutil

    shutil.rmtree(example_dir)
    print("\n✓ Cleaned up example directory")

    # =========================================================================
    # 7. ERROR HANDLING
    # =========================================================================
    print("\n7. Error handling examples...")

    # Try to read non-existent file
    result = await read_file.execute(path="nonexistent.txt")
    print(f"Reading missing file: success={result.success}")
    if not result.success:
        print(f"  Error message: {result.error}")

    # Try to delete non-existent file
    result = await delete_file.execute(path="nonexistent.txt")
    print(f"Deleting missing file: success={result.success}")
    if not result.success:
        print(f"  Error message: {result.error}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
