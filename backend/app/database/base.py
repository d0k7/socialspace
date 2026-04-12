"""
Database Base Configuration
============================
WHY: Centralised declarative base so all models share the same
     metadata object. Alembic reads this metadata to generate migrations.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# WHY this naming convention: PostgreSQL has a 63-char identifier limit.
# Explicit names prevent Alembic from generating truncated constraint names
# that differ between environments, causing silent migration drift.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)