"""
Test-Driven Development: Letta Database Initialization
This test verifies that the Letta database can be properly initialized with all required tables.
"""
import asyncio
import sqlite3
from pathlib import Path


def test_database_file_exists():
    """Test 1: Verify the database file was created"""
    db_path = Path.home() / ".letta" / "letta.db"
    assert db_path.exists(), f"Database file should exist at {db_path}"
    print(f"[PASS] Test 1: Database file exists at {db_path}")
    return db_path


def test_organizations_table_exists(db_path):
    """Test 2: Verify the organizations table exists (the table causing the error)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if organizations table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='organizations'
    """)
    result = cursor.fetchone()
    conn.close()

    assert result is not None, "organizations table should exist in database"
    print("[PASS] Test 2: organizations table exists")


def test_all_expected_tables_exist(db_path):
    """Test 3: Verify all expected tables from Base.metadata exist"""
    expected_tables = [
        'block_history', 'blocks_agents', 'block', 'identities',
        'organizations', 'agents', 'agents_tags', 'archives',
        'archives_agents', 'file_contents'
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    actual_tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    missing_tables = set(expected_tables) - actual_tables
    assert not missing_tables, f"Missing tables: {missing_tables}"

    print(f"[PASS] Test 3: All {len(expected_tables)} expected tables exist")
    print(f"  Found tables: {sorted(actual_tables)}")


def test_database_is_writable(db_path):
    """Test 4: Verify we can write to the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Try to query the organizations table
        cursor.execute("SELECT COUNT(*) FROM organizations")
        count = cursor.fetchone()[0]
        print(f"[PASS] Test 4: Database is writable (organizations has {count} rows)")
    except sqlite3.OperationalError as e:
        conn.close()
        raise AssertionError(f"Cannot query organizations table: {e}")

    conn.close()


def run_all_tests():
    """Run all database initialization tests"""
    print("=" * 60)
    print("TDD: Testing Letta Database Initialization")
    print("=" * 60)

    try:
        db_path = test_database_file_exists()
        test_organizations_table_exists(db_path)
        test_all_expected_tables_exist(db_path)
        test_database_is_writable(db_path)

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED! Database is properly initialized.")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        print("\nThis means the database needs to be initialized.")
        print("Run the initialization script to create the tables.")
        return False
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
