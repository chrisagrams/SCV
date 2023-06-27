from sqlalchemy import Column, Integer, String, Text, DateTime, TypeDecorator, ForeignKey, Double, Boolean, Table, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import json
import uuid
from datetime import datetime

from sqlalchemy.orm import relationship

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
    __tablename__ = 'jobs'

    job_number = Column(StringUUID, primary_key=True, default=uuid.uuid4)
    psms = Column(JSON)
    ptm_annotations = Column(JSON)
    background_color = Column(Integer)
    species = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sequence_coverage_results = relationship('SequenceCoverageResult', secondary='job_seq_result',
                                             back_populates='jobs')

    @classmethod
    def from_model(cls, model):
        return cls(
            job_number=uuid.uuid4(),
            psms=model.psms,
            ptm_annotations=model.ptm_annotations,
            background_color=model.background_color,
            species=model.species
        )


class SequenceCoverageResult(Base):
    __tablename__ = 'sequence_coverage_results'

    id = Column(String, primary_key=True)
    protein_id = Column(Text)
    coverage = Column(Double)
    sequence = Column(Text)
    sequence_coverage = Column(JSON)
    ptms = Column(JSON)
    has_pdb = Column(Boolean)
    jobs = relationship('Job', secondary='job_seq_result', back_populates='sequence_coverage_results')

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            protein_id=model.protein_id,
            coverage=model.coverage,
            sequence=model.sequence,
            sequence_coverage=model.sequence_coverage,
            ptms=model.ptms,
            has_pdb=model.has_pdb
        )

# Job Result and Sequence Coverage Result junction table
job_seq_result = Table(
    'job_seq_result',
    Base.metadata,
    Column('job_number', StringUUID, ForeignKey('jobs.job_number')),
    Column('id', String, ForeignKey('sequence_coverage_results.id'))
)


class FASTA_Entry(Base):
    __tablename__ = 'fasta_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    source_filename = Column(Text)
    data = Column(JSON)


class Access(Base):
    __tablename__ = 'access'

    id = Column(Integer, primary_key=True)
    ip = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    path = Column(String)
    method = Column(String)
