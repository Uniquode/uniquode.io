"""SQLAlchemy ORM model package."""

from uniquode.models.base import Base

metadata = Base.metadata

__all__ = ["Base", "metadata"]
