"""SQLAlchemy declarative base for all PhiGateway ORM models.

All model classes in ``phi_gateway.models`` inherit from this base,
which provides the declarative metadata registry for table creation
and migration.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models.

    Inherit from this class when defining new tables. It carries
    the metadata registry used by Alembic and ``create_all()``.
    """

    pass
