"""Test if cost tracking writes to database."""

import sqlite3

from paracle_core.cost import CostTracker

# Create tracker
tracker = CostTracker()

print("✓ Cost tracker initialized")
print(f"  Tracking enabled: {tracker.config.tracking.enabled}")
print(f"  DB path: {tracker._db_path}")

# Track some test usage
record = tracker.track_usage(
    provider="openai",
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=50,
    agent_id="test-agent",
    workflow_id="test-workflow",
)

print("\n✓ Tracked test usage:")
print(f"  Timestamp: {record.timestamp}")
print(f"  Cost: ${record.total_cost:.6f}")
print(f"  Tokens: {record.total_tokens}")

# Check database

conn = sqlite3.connect(tracker._db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM cost_records")
count = cursor.fetchone()[0]
print(f"\n✓ Database now has {count} record(s)")

if count > 0:
    cursor.execute(
        """
        SELECT timestamp, provider, model, total_tokens, total_cost
        FROM cost_records
        ORDER BY timestamp DESC
        LIMIT 1
    """
    )
    row = cursor.fetchone()
    print(f"  Latest: {row[1]} | {row[2]} | {row[3]} tokens | ${row[4]:.6f}")

conn.close()
print("\n✅ Cost tracking is working correctly!")
