"""Main entry point for SQLAlchemy PostgreSQL practice project."""
from database import init_db


def main():
    """Initialize database and create tables."""
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!")


if __name__ == "__main__":
    main()