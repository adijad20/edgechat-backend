"""Base class for all SQLAlchemy models. All tables inherit from this."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
