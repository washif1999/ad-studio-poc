import os
import libsql_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

def get_db_client():
    if not url or not auth_token:
        raise ValueError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in .env")
    return libsql_client.create_client_sync(url=url, auth_token=auth_token)

def init_db():
    client = get_db_client()
    
    # Create the ads table based on the POC plan
    client.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            status TEXT,
            video_url TEXT,
            current_progress INTEGER DEFAULT 0
        )
    """)
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
