"""Quick script to check costs.db status."""

import sqlite3
from pathlib import Path

db_path = Path(".parac/memory/data/costs.db")

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    exit(1)

print(f"✓ Database found at {db_path}")
print(f"  Size: {db_path.stat().st_size:,} bytes")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"\n📊 Tables: {tables}")

# Get record count
cursor.execute("SELECT COUNT(*) FROM cost_records")
count = cursor.fetchone()[0]
print(f"\n📝 Total cost records: {count}")

if count > 0:
    # Show sample records
    cursor.execute(
        """
        SELECT timestamp, provider, model, total_tokens, total_cost
        FROM cost_records
        ORDER BY timestamp DESC
        LIMIT 5
    """
    )
    print("\n🔍 Recent records:")
    for row in cursor.fetchall():
        print(f"   {row[0]} | {row[1]} | {row[2]} | {row[3]} tokens | ${row[4]:.4f}")

    # Show totals
    cursor.execute("SELECT SUM(total_cost), SUM(total_tokens) FROM cost_records")
    total_cost, total_tokens = cursor.fetchone()
    print("\n💰 Totals:")
    print(f"   Cost: ${total_cost:.4f}")
    print(f"   Tokens: {total_tokens:,}")

conn.close()
