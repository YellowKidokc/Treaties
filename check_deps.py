import sys
print(f"Python {sys.version}")
try:
    import psycopg
    print("psycopg: OK")
except ImportError:
    print("psycopg: NOT INSTALLED")
try:
    import fastapi
    print("fastapi: OK")
except ImportError:
    print("fastapi: NOT INSTALLED")
try:
    import sqlalchemy
    print("sqlalchemy: OK")
except ImportError:
    print("sqlalchemy: NOT INSTALLED")
