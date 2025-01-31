from sqlalchemy import (
    types,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    TypeDecorator,
    ForeignKey,
    Double,
    Boolean,
    Table,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import Mutable
import json
import uuid
import zstd
from datetime import datetime

from sqlalchemy.orm import relationship

Base = declarative_base()


class CompressedText(types.TypeDecorator):
    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = zstd.compress(value.encode())
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = zstd.decompress(value).decode()
        return value


class MutableCompressedText(CompressedText, Mutable):
    pass


class StringUUID(TypeDecorator):
    """
    A type that provides way to store UUID as string in database (for SQLite)
    """

    impl = String(36)
    cache_ok = True  # this type is immutable

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return uuid.UUID(value)
            except ValueError:
                pass
        return None


class UploadedPDB(Base):
    __tablename__ = "uploaded_pdbs"
    id = Column(StringUUID, primary_key=True, default=uuid.uuid4)
    pdb_file = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    filesize = Column(Integer)
    filename = Column(Text)
    pdb_id = Column(Text)
    job_number = Column(StringUUID, ForeignKey("jobs.job_number"), nullable=True)
    job = relationship("Job", back_populates="pdb_file")

    @classmethod
    def from_model(cls, model):
        return cls(
            pdb_file=model.pdb_file,
            filesize=model.filesize,
            filename=model.filename,
            pdb_id=model.pdb_id,
        )


class Job(Base):
    __tablename__ = "jobs"

    job_number = Column(StringUUID, primary_key=True, default=uuid.uuid4)
    psms = Column(JSON)
    ptm_annotations = Column(JSON)
    background_color = Column(Integer)
    species = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    usis = Column(JSON)

    sequence_coverage_results = relationship(
        "SequenceCoverageResult", secondary="job_seq_result", back_populates="jobs"
    )
    pdb_file = relationship("UploadedPDB", back_populates="job")

    @classmethod
    def from_model(cls, model):
        return cls(
            job_number=uuid.uuid4(),
            psms=model.psms,
            ptm_annotations=model.ptm_annotations,
            background_color=model.background_color,
            species=model.species,
            usis=model.usis,
        )


class SequenceCoverageResult(Base):
    __tablename__ = "sequence_coverage_results"

    id = Column(String, primary_key=True)
    protein_id = Column(Text)
    coverage = Column(Double)
    sequence = Column(Text)
    unid = Column(Text)
    description = Column(Text)
    sequence_coverage = Column(JSON)
    ptms = Column(JSON)
    has_pdb = Column(Boolean)
    jobs = relationship(
        "Job", secondary="job_seq_result", back_populates="sequence_coverage_results"
    )

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            protein_id=model.protein_id,
            coverage=model.coverage,
            sequence=model.sequence,
            unid=model.unid,
            description=model.description,
            sequence_coverage=model.sequence_coverage,
            ptms=model.ptms,
            has_pdb=model.has_pdb,
        )


# Job Result and Sequence Coverage Result junction table
job_seq_result = Table(
    "job_seq_result",
    Base.metadata,
    Column("job_number", StringUUID, ForeignKey("jobs.job_number")),
    Column("id", String, ForeignKey("sequence_coverage_results.id")),
)


class ProteinStructure(Base):
    __tablename__ = "protein_structures"

    id = Column(String, primary_key=True)
    protein_id = Column(Text)
    species = Column(Text)
    pdb_id = Column(Text)
    objs = Column(JSON)
    view = Column(JSON)
    amino_ele_pos = Column(JSON)
    pdb_str = Column(MutableCompressedText)

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            protein_id=model.protein_id,
            species=model.species,
            pdb_id=model.pdb_id,
            objs=model.objs,
            view=model.view,
            amino_ele_pos=model.amino_ele_pos,
            pdb_str=model.pdb_str,
        )


class FASTA_Entry(Base):
    __tablename__ = "fasta_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    source_filename = Column(Text)
    data = Column(JSON)


class Access(Base):
    __tablename__ = "access"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    path = Column(String)
    method = Column(String)
    job_number = Column(
        StringUUID, nullable=True
    )  # nullable because some requests don't have job number. No relationship in case of invalid job number.
