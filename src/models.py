import re
from pydantic import BaseModel, ValidationError, validator
from typing import List

class USIModel(BaseModel):
    pxid: str = None
    filename: str = None
    scan: int = None
    psm: str = None
    charge: int = None


class JobModel(BaseModel):
    psms: dict = None
    ptm_annotations: dict = None
    background_color: int = None
    species: str = None
    usis: List[USIModel] = []

    @validator('psms')
    def validate_psms(cls, v):
        if v is None:
            raise ValueError('PSMs must be specified.')
        if not isinstance(v, dict):
            raise ValueError('PSMs must be a dictionary.')
        if len(v) == 0:
            raise ValueError('PSMs must contain at least one group.')

        # Check if all keys are ASCII
        for key in v.keys():
            if not all(ord(c) < 128 for c in key):
                raise ValueError('PSM keys must be ASCII.')

        # Check if all values are lists containing valid peptide sequences (including PTMs)
        for value in v.values():
            if not isinstance(value, list):
                raise ValueError('PSM values must be lists.')
            for item in value:
                if not re.match(r"^([ARNDCQEGHILKMFPSTWYV\[\]\d\.])*$", item) or not re.match(
                        r"(?:[ARNDCQEGHILKMFPSTWYV]+|\[\d+(?:\.\d+)?\])*", item):
                    raise ValueError('PSM values must be lists of valid peptide sequences.')
        return v

    @validator('ptm_annotations')
    def validate_ptm_annotations(cls, v):
        if v is None:
            raise ValueError('PTM annotations must be specified.')
        if not isinstance(v, dict):
            raise ValueError('PTM annotations must be a dictionary.')

        for key in v.keys():
            # Check if all keys are ASCII
            if not all(ord(c) < 128 for c in key):
                raise ValueError('PTM annotation keys must be ASCII.')

        for value in v.values():
            # Check if the value is a list of exactly three integers
            if not isinstance(value, list):
                raise ValueError('PTM annotation values must be lists.')
            if len(value) != 3:
                raise ValueError('PTM annotation values must be lists of length 3.')
            for item in value:
                # Check if the item is an integer and within the range 0-255
                if not isinstance(item, int) or not 0 <= item <= 255:
                    raise ValueError('PTM annotation values must be lists of integers between 0 and 255.')
        return v

    @validator('background_color')
    def validate_background_color(cls, v):
        if v is None:
            raise ValueError('Background color must be specified.')
        if not isinstance(v, int):
            raise ValueError('Background color must be an integer.')
        if v < 0:
            raise ValueError('Background color must be a positive integer.')
        if v > 16777215:
            raise ValueError('Background color must be less than 16777215.')
        return v

    @validator('species')
    def validate_species(cls, v):
        if v is None:
            raise ValueError('Species must be specified.')
        if not isinstance(v, str):
            raise ValueError('Species must be a string.')
        if v not in ['human', 'mouse', 'rat'] and len(v) != 0:
            raise ValueError('Species must be human, mouse, or rat.')
        return v


class UploadedPDBModel(BaseModel):
    id: str = None
    pdb_file: str = None
    filesize: int = None
    filename: str = None
    pdb_id: str = None


class SequenceCoverageModel(BaseModel):
    id: str = None
    protein_id: str = None
    coverage: float = None
    sequence: str = None
    UNID: str = None
    description: str = None
    sequence_coverage: list = None
    ptms: dict = None
    has_pdb: bool = None

    @classmethod
    def from_dict(cls, d):
        try:
            return cls(**d)
        except ValidationError as e:
            raise ValueError(e)

    @classmethod
    def to_dict(cls, obj):
        return {
            'id': obj.id,
            'protein_id': obj.protein_id,
            'coverage': obj.coverage,
            'sequence': obj.sequence,
            'UNID': obj.UNID,
            'description': obj.description,
            'sequence_coverage': obj.sequence_coverage,
            'ptms': obj.ptms,
            'has_pdb': obj.has_pdb
        }


class ProteinStructureModel(BaseModel):
    id: str = None
    protein_id: str = None
    species: str = None
    pdb_id: str = None
    objs: dict = None
    view: dict = None
    amino_ele_pos: dict = None
    pdb_str: str = None

    @classmethod
    def from_dict(cls, d):
        try:
            return cls(**d)
        except ValidationError as e:
            raise ValueError(e)
