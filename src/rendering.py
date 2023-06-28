import pymol  # must be installed on system (see README.md)
from vendor.python.pymol2glmol import *


def setup_pymol(pdb_file, pdb_name):
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


def get_objs(name):
    try:
        cmd.set('pse_export_version', 1.74)
    except:
        pass
    names = cmd.get_session()['names']
    cmd.set('pdb_retain_ids', 1)

    ret = ''

    for obj in names:
        if obj == None:
            continue
        if obj[2] == 0:  # not visible
            continue
        if obj[1] == 0 and obj[4] == 1 and obj[0] == name:
            ret += parseObjMol(obj)
            print(ret)
        if obj[1] == 0 and obj[4] == 4:  # currently all dist objects are exported
            ret += parseDistObj(obj)

    return ret


def show_cov_3D(pdb_file, pdb_name):
    setup_pymol(pdb_file, pdb_name)
    ret = get_objs(pdb_name)
    print(ret)


if __name__ == "__main__":
    pdb_file = "C:\\Users\\Chris\\Downloads\\protein-vis\\Protein-Vis\\pdbs\\UP000000589_10090_MOUSE\\AF-Q99JR5-F1-model_v1.pdb"
    pdb_name = "AF-Q99JR5-F1-model_v1.pdb"
    show_cov_3D(pdb_file, pdb_name)
