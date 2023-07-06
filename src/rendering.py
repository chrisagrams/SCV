import os

import numpy as np
import pymol  # must be installed on system (see README.md)
import re
import time
import sys

from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, Job, SequenceCoverageResult, ProteinStructure
from src.helpers import pymol_obj_extract, pymol_obj_dict_to_str, pymol_view_dict_to_str, color_dict_to_str, calc_hash_of_dict
from src.models import ProteinStructureModel

default_covered = [255, 62, 62]
default_non_covered = [221, 221, 221]


def setup_pymol_from_file(pdb_file, pdb_name):
    # Load the PDB file
    try:
        original_stdout = sys.stdout
        null_device = open(os.devnull, 'w')
        sys.stdout = null_device

        pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
        pymol.finish_launching()
        pymol.cmd.load(pdb_file, pdb_name)
        pymol.cmd.disable("all")
        pymol.cmd.enable()
        pymol.cmd.hide('all')
        pymol.cmd.show('cartoon')
        pymol.cmd.set('ray_opaque_background', 0)
        pymol.cmd.bg_color('black')
        pymol.cmd.set('pse_export_version',
                      1.74)  # set the version of the PyMOL session file to 1.74 (needed for pymol 2.0)
        pymol.cmd.set('pdb_retain_ids', 1)  # keep the original residue ids, not sure if this is necessary
        session = pymol.cmd.get_session(pdb_name, partial=0)  # get PDB session

        sys.stdout = original_stdout
        null_device.close()
    except pymol.CmdException as e:
        print(f'A pymol error occurred: {e}')
    return session


def get_pdb_str_from_file(pdb_file):
    with open(pdb_file, 'r') as f:
        pdb_str = f.read()
    return pdb_str


def setup_pymol_from_string(pdb_str, pdb_name) -> dict:
    # Load the PDB file from string
    try:
        pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
        pymol.finish_launching()
        pymol.cmd.read_pdbstr(pdb_str, pdb_name)
        pymol.cmd.disable("all")
        pymol.cmd.enable()
        pymol.cmd.hide('all')
        pymol.cmd.show('cartoon')
        pymol.cmd.set('ray_opaque_background', 0)
        pymol.cmd.bg_color('black')
        pymol.cmd.set('pse_export_version',
                      1.74)  # set the version of the PyMOL session file to 1.74 (needed for pymol 2.0)
        pymol.cmd.set('pdb_retain_ids', 1)  # keep the original residue ids, not sure if this is necessary
        session = pymol.cmd.get_session(pdb_name, partial=0)  # get PDB session
    except pymol.CmdException as e:
        print(f'A pymol error occurred: {e}')
    return session


def clean_pymol():
    pymol.cmd.delete('all')
    pymol.cmd.quit()


def get_amino_ele_pos_dict(pdb_str) -> dict:
    # from pdb_str get element pos to amino acid pos
    pdb_str = pdb_str.split('\nTER')[0].split('\n')
    amino_ele_pos_dict = defaultdict(list)
    for line in pdb_str:
        amino_ele_pos_dict[int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group())].append(
            int(re.search('\d+', line).group()))
    amino_ele_pos_dict = {each: sorted(amino_ele_pos_dict[each]) for each in amino_ele_pos_dict}

    return amino_ele_pos_dict


def get_annotations(sequence_coverage: list,
                    ptms: dict,
                    ptm_annotations: dict,
                    amino_ele_pos_dict) -> dict:
    # get index of zeros and nonzeros
    np_cov = np.array(sequence_coverage).astype(np.int32)  # convert to numpy array
    non_zero_index = np.nonzero(np_cov)[0]
    zero_index = np.nonzero(np_cov == 0)[0]

    # get index blocks of zeros and nonzeros
    cov_pos_block = np.split(non_zero_index, np.where(np.diff(non_zero_index) != 1)[0] + 1)
    non_cov_pos_block = np.split(zero_index, np.where(np.diff(zero_index) != 1)[0] + 1)

    # add zeros to amino_ele_pos_dict for amino acids not in pdb_str
    for kpos in range(len(sequence_coverage)):
        if kpos + 1 not in amino_ele_pos_dict:
            amino_ele_pos_dict[kpos + 1] = [0]
    amino_ele_pos_dict = {each: sorted(amino_ele_pos_dict[each]) for each in amino_ele_pos_dict}

    non_cov = [(amino_ele_pos_dict[each[0] + 1][0], amino_ele_pos_dict[each[-1] + 1][-1]) for each in non_cov_pos_block]
    cov = [(amino_ele_pos_dict[each[0] + 1][0], amino_ele_pos_dict[each[-1] + 1][-1]) for each in cov_pos_block]

    ptm_color_dict = {}

    if ptms:
        for ptm in ptms:
            # color = [int(each) / 256 for each in ptm_annotations[ptm]]  # List of color values
            ptm_color_dict[ptm] = {}
            ptm_color_dict[ptm]['color'] = ptm_annotations[ptm]

            ptm_color_dict[ptm]['indices'] = [(amino_ele_pos_dict[idx + 1][0], amino_ele_pos_dict[idx + 1][-1])
                                              for idx in ptms[ptm]]  # List of indices

    res = {
        'covered':
            {
                'color': default_covered,
                'indices': cov
            },
        'non_covered':
            {
                'color': default_non_covered,
                'indices': non_cov
            },
    }

    res.update(ptm_color_dict)

    return res


def get_objs(session: dict, pdb_name: str) -> dict:
    # get objects from PDB session
    obj = session['names'][0]

    if obj is None:  # PDB not loaded
        raise Exception('No objects found.')
    if obj[2] == 0:  # not visible
        raise Exception('Object not visible.')
    if obj[1] == 0 and obj[4] == 1 and obj[0] == pdb_name:
        return pymol_obj_extract(obj)

    raise Exception('Unknown error')


def get_view() -> dict:
    # pymol.cmd.turn('z', 180)
    view = pymol.cmd.get_view()
    # pymol.cmd.turn('z', 180)

    # view = session['view']

    ret = {
        'rotation_matrix': {
            # | n11 n12 n13 |
            # | n21 n22 n23 |
            # | n31 n32 n33 |
            'n11': view[0],
            'n21': view[1],
            'n31': view[2],
            'n12': view[3],
            'n22': view[4],
            'n32': view[5],
            'n13': view[6],
            'n23': view[7],
            'n33': view[8],
        },
        'cx': -view[12],  # cx
        'cy': -view[13],  # cy
        'cz': -view[14],  # cz
        'camera_z': -view[11] - 150,  # camera_z
        'slab_near': view[15] + view[11],  # slab_near
        'slab_far': view[16] + view[11],  # slab_far
        'fog_start': float(pymol.cmd.get("fog_start")),  # fog_start
        'fov': float(pymol.cmd.get("field_of_view")),  # fov
    }
    return ret


def render_3d_from_pdb(pdb_file: str,
                       pdb_name: str) -> dict:
    """
    Generate GLmol string for 3D visualization of protein coverage
    """
    pymol_session = setup_pymol_from_file(pdb_file, pdb_name)  # setup pymol + load pdb
    pdb_str = pymol.cmd.get_pdbstr(pdb_name)  # get pdb string

    objs = get_objs(pymol_session, pdb_name)

    view = get_view()

    amino_ele_pos = get_amino_ele_pos_dict(pdb_str)

    # annotations = get_annotations(sequence_coverage, ptms, ptm_annotations, amino_ele_pos)

    clean_pymol() # clean up pymol session

    return {
        'objs': objs,
        'view': view,
        'amino_ele_pos': amino_ele_pos,
        # 'annotations': annotations
    }


def get_db_model_from_pdb(pdb_file, pdb_name, protein_id, species) -> ProteinStructure:
    ret = render_3d_from_pdb(pdb_file, pdb_name)
    protein_model = ProteinStructureModel.from_dict(ret)
    protein_model.protein_id = protein_id
    protein_model.pdb_id = pdb_name.split('.')[0]
    protein_model.id = calc_hash_of_dict(ret)
    protein_model.species = species
    return ProteinStructure.from_model(protein_model)


if __name__ == "__main__":
    pdb_file = "C:\\Users\\cgrams\\protein-vis\\Protein-Vis\\pdbs\\UP000000589_10090_MOUSE\\AF-Q99JR5-F1-model_v1.pdb"
    pdb_name = "AF-Q99JR5-F1-model_v1.pdb"

    db_start = time.time()
    engine = create_engine('sqlite:///../db/dev.db')  # create SQLAlchemy engine

    Base.metadata.create_all(engine)  # create database tables

    Session = sessionmaker(bind=engine)  # create session factory

    session = Session()

    job = session.query(Job).filter(Job.job_number == '03028b4d-f9d4-4a20-893c-fb344d6441e6').first()

    seq_result = session.query(SequenceCoverageResult).filter(SequenceCoverageResult.protein_id == "Q99JR5").first()

    print(time.time() - db_start)

    # get_objs(pdb_name)

    start = time.time()
    ret = render_3d_from_pdb(pdb_file,
                             pdb_name,
                             )

    hsh = calc_hash_of_dict(ret)

    # protein_model = ProteinStructureModel.from_dict(ret)
    #
    # protein_model.protein_id = seq_result.protein_id
    # protein_model.pdb_id = 'AF-Q99JR5-F1-model_v1'
    # protein_model.id = hsh
    # protein_model.species = "mouse"
    #
    # protein_db_model = ProteinStructure.from_model(protein_model)
    # session.add(protein_db_model)
    # session.commit()
    # session.close()


    print(ret)

    print(time.time() - start)

