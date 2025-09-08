from functools import reduce
from uuid import uuid4

from sqlalchemy import Column, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Mapped

metadata = MetaData()

@as_declarative(metadata=metadata)
class Base:
    """
    Base class to handle table schema
    """

    __name__: str

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
