from sqlalchemy import Column, Integer, String, Text, DateTime, TypeDecorator, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import json
import uuid
from datetime import datetime

Base = declarative_base()


class StringUUID(TypeDecorator):
    '''
    A type that provides way to store UUID as string in database (for SQLite)
    '''
    impl = String(36)
    cache_ok = True  # this type is immutable

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return uuid.UUID(value)


class Job(Base):
    __tablename__ = 'requests'

    job_number = Column(StringUUID, primary_key=True, default=uuid.uuid4)
    psms = Column(Text)
    ptm_annotations = Column(Text)
    background_color = Column(Integer)
    species = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def from_model(cls, model):
        return cls(
            psms=json.dumps(model.psms),
            ptm_annotations=json.dumps(model.ptm_annotations),
            background_color=model.background_color,
            species=model.species
        )

class JobResult(Base):
    job_number = Column(StringUUID, primary_key=True)
    pq = Column(Text)
    id_ptm_idx_dict = Column(Text)
    regex_dict = Column(Text)
    background_color = Column(Integer)
    structures = ForeignKey('structures.id')

class Access(Base):
    __tablename__ = 'access'

    id = Column(Integer, primary_key=True)
    ip = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    path = Column(String)
    method = Column(String)
