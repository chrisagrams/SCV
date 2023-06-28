import numpy as np
import pymol  # must be installed on system (see README.md)
import re
import time

from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, Job, SequenceCoverageResult
from helpers import pymol_obj_extract, pymol_obj_dict_to_str, pymol_view_dict_to_str


def setup_pymol_from_file(pdb_file, pdb_name):
    # Load the PDB file
    pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
    pymol.finish_launching()
    pymol.cmd.load(pdb_file, pdb_name)
    pymol.cmd.disable("all")
    pymol.cmd.enable()
    pymol.cmd.hide('all')
    pymol.cmd.show('cartoon')
    pymol.cmd.set('ray_opaque_background', 0)
    pymol.cmd.bg_color('black')


def get_pdb_str_from_file(pdb_file):
    with open(pdb_file, 'r') as f:
        pdb_str = f.read()
    return pdb_str


def setup_pymol_from_string(pdb_str, pdb_name):
    # Load the PDB file from string
    pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
    pymol.finish_launching()
    pymol.cmd.read_pdbstr(pdb_str, pdb_name)
    pymol.cmd.disable("all")
    pymol.cmd.enable()
    pymol.cmd.hide('all')
    pymol.cmd.show('cartoon')
    pymol.cmd.set('ray_opaque_background', 0)
    pymol.cmd.bg_color('black')


def color_getter(sequence_coverage: list,
                 ptms: dict,
                 ptm_annotations: dict,
                 pdb_str: str) -> str:
    # from pdb_str get element pos to amino acid pos
    pdb_str = pdb_str.split('\nTER')[0].split('\n')
    amino_ele_pos_dict = defaultdict(list)
    for line in pdb_str:
        amino_ele_pos_dict[int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group())].append(
            int(re.search('\d+', line).group()))
    amino_ele_pos_dict = {each: sorted(amino_ele_pos_dict[each]) for each in amino_ele_pos_dict}
    for kpos in range(len(sequence_coverage)):
        if kpos + 1 not in amino_ele_pos_dict:
            amino_ele_pos_dict[kpos + 1] = [0]
    amino_ele_pos_dict = {each: sorted(amino_ele_pos_dict[each]) for each in amino_ele_pos_dict}

    default = 'color:0.863,0.863,0.863:'  # grey
    covered = 'color:1.000,0.243,0.243:'
    # get index of zeros and nonzeros
    sequence_coverage = np.array(seq_result.sequence_coverage).astype(np.int32)  # convert to numpy array
    non_zero_index = np.nonzero(sequence_coverage)[0]
    zero_index = np.nonzero(sequence_coverage == 0)[0]

    # get index blocks of zeros and nonzeros
    cov_pos_block = np.split(non_zero_index, np.where(np.diff(non_zero_index) != 1)[0] + 1)
    non_cov_pos_block = np.split(zero_index, np.where(np.diff(zero_index) != 1)[0] + 1)

    # string concatenate
    default += ','.join([str(amino_ele_pos_dict[each[0] + 1][0]) + '-' + str(amino_ele_pos_dict[each[-1] + 1][-1])
                         for each in non_cov_pos_block])
    covered += ','.join([str(amino_ele_pos_dict[each[0] + 1][0]) + '-' + str(amino_ele_pos_dict[each[-1] + 1][-1])
                         for each in cov_pos_block])

    # ptm color string concatenate
    ptm_color = ''
    if ptms:
        for ptm in ptms:
            ptm_color += 'color:' + ','.join(
                ['%.3f' % (int(each) / 256) for each in ptm_annotations[ptm]]) + ':'
            ptm_color += ','.join([str(amino_ele_pos_dict[idx + 1][0]) + '-'
                                   + str(amino_ele_pos_dict[idx + 1][-1])
                                   for idx in ptms[ptm]])
            ptm_color += '\n'
    return default + '\n' + covered + '\n' + ptm_color.rstrip('\n')


def get_objs(pdb_name: str) -> str:
    try:
        pymol.cmd.set('pse_export_version', 1.74)
        pymol.cmd.set('pdb_retain_ids', 1)  # keep the original residue ids, not sure if this is necessary
    except pymol.CmdException as e:
        print(f'A pymol error occurred: {e}')

    names = pymol.cmd.get_session()['names']

    for obj in names:
        if obj is None:
            continue
        if obj[2] == 0:  # not visible
            continue
        if obj[1] == 0 and obj[4] == 1 and obj[0] == pdb_name:
            return pymol_obj_extract(obj)

    raise Exception('No objects found')


def get_view() -> dict:
    pymol.cmd.turn('z', 180)
    view = pymol.cmd.get_view()
    pymol.cmd.turn('z', 180)

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


def show_cov_3D(pdb_file: str,
                pdb_name: str,
                sequence_coverage: list,
                ptms: dict,
                ptm_annotations: dict,
                background_color: int) -> str:
    """
    Generate GLmol string for 3D visualization of protein coverage
    """
    setup_pymol_from_file(pdb_file, pdb_name)  # setup pymol + load pdb
    pdb_str = pymol.cmd.get_pdbstr(pdb_name)  # get pdb string

    objs = get_objs(pdb_name)

    view = get_view()

    ret = pymol_obj_dict_to_str(objs) \
          + color_getter(sequence_coverage, ptms, ptm_annotations, pdb_str) \
          + pymol_view_dict_to_str(view) \
          + f"bgcolor:{background_color}"

    return ret


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
    ret = show_cov_3D(pdb_file,
                      pdb_name,
                      seq_result.sequence_coverage,
                      seq_result.ptms,
                      job.ptm_annotations,
                      job.background_color
                      )

    print(ret)

    print(time.time() - start)
