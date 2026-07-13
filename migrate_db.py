import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database
from alembic.config import Config
from alembic import command

def migrate():
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")

    # Convert asyncpg to psycopg2 for management if necessary
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(sync_url)

    # 1. Create database if it doesn't exist
    try:
        if not database_exists(engine.url):
            print(f"Creating database: {engine.url.database}")
            create_database(engine.url)
        else:
            print(f"Database {engine.url.database} already exists.")
    except Exception as e:
        print(f"Error checking/creating database: {e}")

    # 2. Run migrations
    print("Running Alembic migrations...")
    alembic_cfg = Config("alembic.ini")
    
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        conn.commit()

    try:
        command.upgrade(alembic_cfg, "head")
        print("Migration complete.")
    except Exception as e:
        print(f"Error running migrations: {e}")

    # 3. Run kitchen migration SQL
    print("Running custom kitchen migrations...")
    try:
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "kitchen_migration.sql")
        if os.path.exists(migration_file):
            with open(migration_file, "r") as f:
                sql = f.read()
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("Custom kitchen migrations applied successfully.")
    except Exception as e:
        print(f"Error running custom kitchen migrations: {e}")

    # 4. Update ENUMs (must be run outside transaction blocks in some PG versions)
    print("Updating ENUM types...")
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            enum_values = [
                'ordering', 'ordered', 'ready', 'eating', 'bill_requested', 'held'
            ]
            for val in enum_values:
                try:
                    conn.execute(text(f"ALTER TYPE table_status_enum ADD VALUE IF NOT EXISTS '{val}';"))
                except Exception as e:
                    print(f"Enum value '{val}' might already exist or error: {e}")
        print("ENUM updates completed.")
    except Exception as e:
        print(f"Error updating ENUMs: {e}")

    # 5. Run table management migration SQL
    print("Running table management migrations...")
    try:
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "table_management_migration.sql")
        if os.path.exists(migration_file):
            with open(migration_file, "r") as f:
                sql = f.read()
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("Table management migrations applied successfully.")
    except Exception as e:
        print(f"Error running table management migrations: {e}")

    # 6. Run floor plan migration SQL
    print("Running floor plan migrations...")
    try:
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "floor_plan_migration.sql")
        if os.path.exists(migration_file):
            with open(migration_file, "r") as f:
                sql = f.read()
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("Floor plan migrations applied successfully.")
    except Exception as e:
        print(f"Error running floor plan migrations: {e}")

    # 7. Run multi-branch migration SQL
    print("Running multi-branch migrations...")
    try:
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "multi_branch.sql")
        if os.path.exists(migration_file):
            with open(migration_file, "r") as f:
                sql = f.read()
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print("Multi-branch migrations applied successfully.")
    except Exception as e:
        print(f"Error running multi-branch migrations: {e}")

if __name__ == "__main__":
    migrate()
