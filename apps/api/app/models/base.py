"""Base Declarative Class for SQLAlchemy models."""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import JSON

class Base(DeclarativeBase):
    """Base SQLAlchemy model with common configuration."""
    type_annotation_map = {
        dict: JSON
    }
