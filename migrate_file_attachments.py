import sqlite3
from pathlib import Path

# Database connection
conn = sqlite3.connect('chat_app.db')
cursor = conn.cursor()

print("Adding file_attachments table...")

try:
    # Create file_attachments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    print("✅ file_attachments table created")

    # Create uploads directory
    upload_dir = Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    print("✅ static/uploads directory created")

    conn.commit()
    print("\n✅ Migration complete!")

except sqlite3.OperationalError as e:
    print(f"⚠️  {e}")

finally:
    conn.close()
