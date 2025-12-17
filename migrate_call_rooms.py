"""
Database migration: Create call_rooms table and call_room_members association table
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('chat_app.db')
    cursor = conn.cursor()

    try:
        # Create call_rooms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                created_by INTEGER,
                is_public BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # Create call_room_members association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_room_members (
                call_room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (call_room_id, user_id),
                FOREIGN KEY (call_room_id) REFERENCES call_rooms(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create default public call room
        cursor.execute("""
            INSERT OR IGNORE INTO call_rooms (name, slug, is_public)
            VALUES ('Algemene Call', 'general-call', 1)
        """)

        conn.commit()
        print("✅ call_rooms table created")
        print("✅ call_room_members table created")
        print("✅ Default 'Algemene Call' room created")

    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
