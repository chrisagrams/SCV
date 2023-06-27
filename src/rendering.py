import pymol  # must be installed on system (see README.md)
from pymol import cmd
from datetime import time


def compactSeq(seq):
    seq.sort()
    ret = []
    prev = -9999
    start = -9999
    seq.append(-1)
    i = 0
    while (i < len(seq) - 1):
        if (start >= 0):
            if (seq[i] + 1 != seq[i + 1]):
                ret.append("%d-%d" % (start, seq[i]))
                start = -999
        else:
            if (seq[i] + 1 != seq[i + 1]):
                start = -999
                ret.append(str(seq[i]))
            else:
                start = seq[i]
        i += 1
    return ','.join(ret)

def parseObjMol(obj):
    name = obj[0]
    ids = []
    sphere = []
    trace = []
    ribbon = []
    stick = []
    surface = []
    line = []
    cross = []
    smallSphere = []
    helix = []
    sheet = []
    colors = {}
    for atom in obj[5][7]:
        rep = atom[20]
        serial = atom[22]
        ss = atom[10]
        bonded = (atom[25] == 1)
        if (rep[5] == 1):
            ribbon.append(serial)
        if (rep[1] == 1):
            sphere.append(serial)
        if (rep[2] == 1):
            surface.append(serial)
        if (rep[7] == 1):
            line.append(serial)
        if (rep[6] == 1):
            trace.append(serial)
        if (rep[4] == 1 and not bonded):
            smallSphere.append(serial)
        if (rep[11] == 1 and not bonded):
            cross.append(serial)
        if (rep[0] == 1 and bonded):
            stick.append(serial)
        if (ss == 'S'):
            sheet.append(serial)
        if (ss == 'H'):
            helix.append(serial)

        c =  cmd.get_color_tuple(atom[21])
        if (not c in colors):
            colors[c] = []
        colors[c].append(serial)
        ids.append("ID %d is %s in resi %s %s at chain %s"\
                       % (atom[22], atom[6], atom[3], atom[5], atom[1]))

    for c in colors.iterkeys(): # TODO: better compression
        colors[c] = compactSeq(colors[c])

    ret = ''
    ret += "\nsheet:" + compactSeq(sheet)
    ret += "\nhelix:" + compactSeq(helix)
    ret += "\nsurface:" + compactSeq(surface)
    ret += "\nsphere:" + compactSeq(sphere)
    ret += "\ntrace:" + compactSeq(trace)
    ret += "\nribbon:" + compactSeq(ribbon)
    ret += "\nstick:" + compactSeq(stick)
    ret += "\nline:" + compactSeq(line)
    ret += "\nsmallSphere:" + compactSeq(smallSphere)
    ret += "\ncross:" + compactSeq(cross)
    for c in colors.iterkeys():
        ret += "\ncolor:%.3f,%.3f,%.3f:%s" % (c[0], c[1], c[2], colors[c])
    return ret

def parseDistObj(obj):
    if (obj[5][0][3][10] != 1): # 'show dashed' flag
        return ""
    N = obj[5][2][0][0]
    points = obj[5][2][0][1]
    ret = []
    for p in points:
        ret.append("%.3f" % p)
    color = cmd.get_color_tuple(obj[5][0][2]);
    return "\ndists:%.3f,%.3f,%.3f:" % color + ','.join(ret)

def setup_pymol(pdb_file, pdb_name):
    # Load the PDB file
    pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
    pymol.finish_launching()
    pymol.cmd.load(pdb_file, pdb_name)
    pymol.cmd.disable("all")
    pymol.cmd.enable
    # pymol.cmd.hide('all')
    pymol.cmd.show('cartoon')
    pymol.cmd.set('ray_opaque_background', 0)
    pymol.cmd.bg_color('black')

def get_objs(name):
    names = cmd.get_session()['names']
    cmd.set('pdb_retain_ids', 1)

    ret = ''

    # for obj in names:
    #     if obj == None:
    #         continue
    #     if obj[2] == 0:  # not visible
    #         continue
    #     if obj[1] == 0 and obj[4] == 1 and obj[0] == name:
    #         ret += parseObjMol(obj)
    #         print(ret)
    #     if obj[1] == 0 and obj[4] == 4:  # currently all dist objects are exported
    #         ret += parseDistObj(obj)

    ret += parseObjMol(names[1])
    #
    return ret
def show_cov_3D(pdb_file, pdb_name):
    setup_pymol(pdb_file, pdb_name)
    ret = get_objs(pdb_name)
    print(ret)


if __name__ == "__main__":
    pdb_file = "C:\\Users\\cgrams\\protein-vis\\Protein-Vis\\pdbs\\UP000000589_10090_MOUSE\\AF-Q99JR5-F1-model_v1.pdb"
    pdb_name = "AF-Q99JR5-F1-model_v1"
    show_cov_3D(pdb_file, pdb_name)
