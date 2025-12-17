"""
Database migration: Add public_key field to User model for E2E encryption
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()

    try:
        # Add public_key column to users table
        cursor.execute("""
            ALTER TABLE users ADD COLUMN public_key TEXT
        """)

        conn.commit()
        print("✅ Added public_key column to users table")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️  public_key column already exists")
        else:
            print(f"❌ Error: {e}")
            raise
    finally:
        conn.close()

    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
