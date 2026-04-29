import psycopg
import sys

creds = [
    ("postgres", "Moss9pep28$", "postgres"),
    ("root", "Moss9pep28$", "postgres"),
    ("Yellowkid", "Moss9pep28$", "postgres"),
    ("kj", "Moss9pep28$", "kj"),
]

for user, pw, db in creds:
    try:
        conn = psycopg.connect(f"postgresql://{user}:{pw}@192.168.1.177:2665/{db}", autocommit=True, connect_timeout=5)
        print(f"SUCCESS: {user}@{db} works!")
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'treaties'")
        if cur.fetchone():
            print("  treaties db already exists")
        else:
            cur.execute("CREATE DATABASE treaties")
            print("  Created treaties db")
        cur.close()
        conn.close()
        
        # Write working .env
        with open(".env", "w") as f:
            f.write(f"DATABASE_URL=postgresql+psycopg://{user}:{pw}@192.168.1.177:2665/treaties\n")
            f.write("OLLAMA_BASE_URL=http://localhost:11434\n")
            f.write("OLLAMA_MODEL=gemma:latest\n")
            f.write("OLLAMA_TIMEOUT_SECONDS=180\n")
            f.write("APP_HOST=127.0.0.1\n")
            f.write("APP_PORT=8000\n")
            f.write("SNAPSHOT_DIR=./snapshots\n")
        print(f"  Updated .env with {user} credentials")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {user}@{db} -> {e}")

print("No credentials worked")
sys.exit(1)
