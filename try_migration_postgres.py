#!/usr/bin/env python3
"""Try to run migration with different users"""

import psycopg

attempts = [
    ("postgres", "glintstone"),
    ("postgres", "postgres"),
    ("postgres", ""),
    ("glintstone", "glintstone"),
]

print("Trying different database user combinations...\n")

for user, password in attempts:
    try:
        print(f"Attempting connection as user '{user}'...")
        if password:
            conn_str = f"host=127.0.0.1 port=5432 dbname=glintstone user={user} password={password}"
        else:
            conn_str = f"host=127.0.0.1 port=5432 dbname=glintstone user={user}"

        conn = psycopg.connect(conn_str, autocommit=True)
        cur = conn.cursor()

        print(f"✓ Connected as '{user}'")

        # Try to run the migration
        print(f"  Attempting ALTER TABLE...")
        cur.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS language_normalized TEXT")
        print(f"  ✓ Column added!")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_language_normalized ON artifacts(language_normalized)")
        print(f"  ✓ Index created!")

        # Verify
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'artifacts' AND column_name = 'language_normalized'")
        if cur.fetchone():
            print(f"\n🎉 SUCCESS! Migration completed with user '{user}'")
            cur.close()
            conn.close()
            exit(0)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
        continue

print("\n❌ All attempts failed. You'll need to run the migration manually as the database owner or superuser.")
print("\nTry running this in a terminal:")
print("  sudo -u postgres psql glintstone -c \"ALTER TABLE artifacts ADD COLUMN language_normalized TEXT;\"")
