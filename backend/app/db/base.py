"""Base class every ORM model inherits from."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
