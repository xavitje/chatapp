import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('chat_app.db')
cursor = conn.cursor()

print("Adding new columns to database...")

try:
    # Add columns to users table
    cursor.execute("ALTER TABLE users ADD COLUMN last_seen DATETIME")
    print("✅ Added users.last_seen")
except sqlite3.OperationalError as e:
    print(f"⚠️  users.last_seen: {e}")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_online BOOLEAN DEFAULT 0")
    print("✅ Added users.is_online")
except sqlite3.OperationalError as e:
    print(f"⚠️  users.is_online: {e}")

try:
    # Add column to rooms table
    cursor.execute("ALTER TABLE rooms ADD COLUMN description TEXT DEFAULT ''")
    print("✅ Added rooms.description")
except sqlite3.OperationalError as e:
    print(f"⚠️  rooms.description: {e}")

try:
    # Add columns to messages table
    cursor.execute("ALTER TABLE messages ADD COLUMN edited_at DATETIME")
    print("✅ Added messages.edited_at")
except sqlite3.OperationalError as e:
    print(f"⚠️  messages.edited_at: {e}")

try:
    cursor.execute("ALTER TABLE messages ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
    print("✅ Added messages.is_deleted")
except sqlite3.OperationalError as e:
    print(f"⚠️  messages.is_deleted: {e}")

try:
    cursor.execute("ALTER TABLE messages ADD COLUMN reply_to_id INTEGER")
    print("✅ Added messages.reply_to_id")
except sqlite3.OperationalError as e:
    print(f"⚠️  messages.reply_to_id: {e}")

# Commit changes
conn.commit()
conn.close()

print("\n✅ Migration complete!")
