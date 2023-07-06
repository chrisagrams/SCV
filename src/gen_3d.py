import pymol
import numpy as np
from collections import defaultdict

from vendor.python.pymol2glmol import *
import ahocorasick
import os
import time
import re



def automaton_trie(peptide_list):
    A = ahocorasick.Automaton()
    for idx, peptide in enumerate(peptide_list):
        A.add_word(peptide, (idx, peptide))
    A.make_automaton()
    return A


def automaton_matching(A, seq_line):
    result = []
    for end_idx, (insert_order, original_value) in A.iter(seq_line):
        start_idx = end_idx - len(original_value) + 1
        result.append((start_idx, end_idx, original_value))
        assert seq_line[start_idx:start_idx + len(original_value)] == original_value
    return result


def fasta_reader(fasta_file_path):
    with open(fasta_file_path, 'r') as file_open:
        file_split = file_open.read().split('\n>')

    return {each.split('\n')[0].split('|')[1]: ''.join(each.split('\n')[1:]) for each in file_split}


def peptide_counting(peptide_tsv_file):
    with open(peptide_tsv_file, 'r') as file_open:
        next(file_open)

        peptide_list = [line.split("\t")[0] for line in file_open]
    return peptide_list


def my_replace(match_obj):
    match_obj = match_obj.group()
    return match_obj[0]  # gives back the first element of matched object as string


def freq_array_and_PTM_index_generator(peptide_list, protein_seq_string, regex_pat='\w{1}\[\d+\.?\d+\]'):
    """
    map single protein seq
    :param peptide_list:
    :param protein_seq_string:
    :param regex_pat:
    :return:
    """

    freq_array = np.zeros(len(protein_seq_string))
    PTM_sites_counting = defaultdict(int)
    PTM_loc_list = []

    # reformat the peptide with PTM numbers into characters only
    new_pep_list = [re.sub(regex_pat, my_replace, pep) for pep in peptide_list]
    PTM_list = [re.findall(regex_pat, pep) for pep in peptide_list]
    # print (PTM_list)
    # calculation

    for pep, new_pep, PTM in zip(peptide_list, new_pep_list, PTM_list):  # PTM_list is list of list
        if new_pep in protein_seq_string:

            start_pos = protein_seq_string.find(new_pep)
            end_pos = start_pos + len(new_pep) - 1
            # print (start_pos,end_pos,new_pep)
            freq_array[start_pos:end_pos + 1] += 1
            if PTM:  # the peptide has ptm site
                for ele in PTM:
                    PTM_index = pep.find(ele)
                    # PTM_site = pep[PTM_index] # single amino acid
                    PTM_sites_counting[ele] += 1
                    PTM_loc_list.append(start_pos + PTM_index)
    # print (PTM_sites_counting, PTM_loc_list)

    return freq_array, PTM_loc_list, PTM_sites_counting


def modified_peptide_from_psm(psm_path):
    psm_list = []
    with open(psm_path, 'r') as f_open:
        next(f_open)
        for line in f_open:
            line_split = line.split('\t')
            match = re.search('\w{1}\[\d+\.?\d+\]', line)
            if match:
                psm_list.append(line_split[3])
            else:
                psm_list.append(line_split[2])
    return psm_list


def color_getter(freq_array, ptm_idx_dict, regex_color_dict, pdb_str):
    """
    based on numpy array get blocks of zeros and non_zeros, generate color string for GLMOL
    :param freq_array: numpy array
    :param pdb_str: cmd.get_pdbstr()
    :return:
    """
    import re
    import numpy as np
    from collections import defaultdict

    # from pdb_str get element pos to amino acid pos
    pdb_str = pdb_str.split('\nTER')[0].split('\n')
    amino_ele_pos_dict = defaultdict(list)
    for line in pdb_str:
        amino_ele_pos_dict[int(re.search('\d+(?=\s+[+-]?\d+\.)', line).group())].append(
            int(re.search('\d+', line).group()))
    amino_ele_pos_dict = {each: sorted(amino_ele_pos_dict[each]) for each in amino_ele_pos_dict}
    for kpos in range(len(freq_array)):
        if kpos+1 not in amino_ele_pos_dict:
            amino_ele_pos_dict[kpos+1]=[0]
    amino_ele_pos_dict = {each: sorted(amino_ele_pos_dict[each]) for each in amino_ele_pos_dict}
    print("aa ele pos dict",amino_ele_pos_dict)
    defalt = 'color:0.863,0.863,0.863:'  # grey
    covered = 'color:1.000,0.243,0.243:'
    # get index of zeros and nonzeros
    non_zero_index = np.nonzero(freq_array)[0]
    zero_index = np.nonzero(freq_array == 0)[0]

    # get index blocks of zeros and nonzeros
    cov_pos_block = np.split(non_zero_index, np.where(np.diff(non_zero_index) != 1)[0] + 1)
    non_cov_pos_block = np.split(zero_index, np.where(np.diff(zero_index) != 1)[0] + 1)
    print(cov_pos_block, non_cov_pos_block)

    # string concatenate
    defalt += ','.join([str(amino_ele_pos_dict[each[0] + 1][0]) + '-' + str(amino_ele_pos_dict[each[-1] + 1][-1])
                        for each in non_cov_pos_block])
    covered += ','.join([str(amino_ele_pos_dict[each[0] + 1][0]) + '-' + str(amino_ele_pos_dict[each[-1] + 1][-1])
                         for each in cov_pos_block])

    # ptm color string concatenate
    ptm_color = ''
    if ptm_idx_dict:
        for ptm in ptm_idx_dict:
            ptm_color += 'color:' + ','.join(
                ['%.3f' % (int(each) / 256) for each in regex_color_dict[ptm]]) + ':'
            ptm_color += ','.join([str(amino_ele_pos_dict[idx + 1][0]) + '-'
                                   + str(amino_ele_pos_dict[idx + 1][-1])
                                   for idx in ptm_idx_dict[ptm]])
            ptm_color += '\n'
    return defalt + '\n' + covered + '\n' + ptm_color.rstrip('\n')


def dump_rep_server(name, freq_array, ptm_idx_dict, regex_color_dict, bg_color):
    if 'PYMOL_GIT_MOD' in os.environ:
        import shutil
        try:
            shutil.copytree(os.path.join(os.environ['PYMOL_GIT_MOD'], 'pymol2glmol', 'js'),
                            os.path.join(os.getcwd(), 'js'))
        except OSError:
            pass
    try:
        cmd.set('pse_export_version', 1.74)
    except:
        pass
    names = cmd.get_session()['names']
    cmd.set('pdb_retain_ids', 1)


    ret = ''
    for obj in names:
        if (obj == None):
            continue
        if (obj[2] == 0):  # not visible
            continue
        if (obj[1] == 0 and obj[4] == 1 and obj[0] == name):
            ret += parseObjMol(obj)
            print(ret)
        if (obj[1] == 0 and obj[4] == 4):  # currently all dist objects are exported
            ret += parseDistObj(obj)

    start = time.time()
    pdb_str = cmd.get_pdbstr(name)
    print(f'time used for pbdstr: {time.time() - start}')

    start = time.time()
    ret += '\n' + color_getter(freq_array, ptm_idx_dict, regex_color_dict, pdb_str)
    print(f'time used for color_getter: {time.time() - start}')

    cmd.turn('z', 180)
    view = cmd.get_view()
    cmd.turn('z', 180)
    cx = -view[12]
    cy = -view[13]
    cz = -view[14]
    cameraZ = - view[11] - 150
    fov = float(cmd.get("field_of_view"))
    fogStart = float(cmd.get("fog_start"))
    slabNear = view[15] + view[11]
    slabFar = view[16] + view[11]
    ret += "\nview:%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % \
           (cx, cy, cz, cameraZ, slabNear, slabFar, fogStart, fov)
    for i in range(9):
        ret += ",%.3f" % view[i]

    ret += "\nbgcolor:" + bg_color
    # bgcolor = cmd.get_setting_tuple('bg_rgb')[1]
    #
    # if len(bgcolor) == 1:
    #     bgcolor = cmd.get_color_tuple(bgcolor[0])
    #
    # ret += "\nbgcolor:%02x%02x%02x" % (int(255 * float(bgcolor[0])), \
    #                                    int(255 * float(bgcolor[1])), int(255 * float(bgcolor[2])))
    # if 'PYMOL_GIT_MOD' in os.environ:
    #     template = open(os.path.join(os.environ['PYMOL_GIT_MOD'], 'pymol2glmol', 'imported.html')).read().\
    #         replace("###INCLUDE_PDB_FILE_HERE###", pdb_str).\
    #         replace('###INCLUDE_REPRESENTATION_HERE###', ret)
    # else:
    #     template = open('imported.html').read().\
    #         replace("###INCLUDE_PDB_FILE_HERE###", pdb_str).\
    #         replace('###INCLUDE_REPRESENTATION_HERE###',ret)
    #
    # if base_path:
    #     f = open(base_path+name + '.html', 'w')
    #     print (f'html file to {base_path+name}.html')
    # else:
    #     f = open(name.split('-')[1] + '.html', 'w')
    #     print ('html file to %s' % name.split('-')[1]+'.html')
    # f.write(template)
    # f.close()

    #     dict = {'pbdstr': cmd.get_pdbstr(name), 'ret': ret}
    dict = {'pbdstr': pdb_str, 'ret': ret}

    # with open(base_path + '.json', 'w') as f:
    #     json.dump(dict, f)
    # pymol.cmd.quit()

    return dict


def show_cov_3d_v2(protein_id,
                   job_number,
                   pdb_file,
                   frequency_array,
                   id_ptm_idx_dict,
                   regex_color_dict=None,
                   png_sava_path=None,
                   base_path=None,
                   background_color='black'):
    """

    :param peptide_list:
    :param protein_seq:
    :param pdb_file:
    :param id_freq_array_dict: returned by freq_ptm_index_gen_batch_v2
    :param id_ptm_idx_dict: returned by freq_ptm_index_gen_batch_v2
    :param png_sava_path:
    :param base_path: html output base path
    :return:
    """
    time_start = time.time()
    if id_ptm_idx_dict != {}:
        ptm_nonzero_idx_dict = id_ptm_idx_dict
    else:
        ptm_nonzero_idx_dict = None

    pdb_name = os.path.split(pdb_file)[1]
    print(pdb_name)
    pymol.pymol_argv = ['pymol', '-qc']  # pymol launching: quiet (-q), without GUI (-c)
    pymol.finish_launching()
    pymol.cmd.load(pdb_file, pdb_name)
    pymol.cmd.disable("all")
    pymol.cmd.enable()
    print(pymol.cmd.get_names())
    pymol.cmd.hide('all')
    pymol.cmd.show('cartoon')
    pymol.cmd.set('ray_opaque_background', 0)
    pymol.cmd.bg_color('black')
    print(f'time used for preproccessing: {time.time() - time_start}')

    if png_sava_path:
        pymol.cmd.png(png_sava_path)

    print(f'image saved to {png_sava_path}')

    print(f'time used for mapping: {pdb_name, time.time() - time_start}')
    # Get out!
    # pymol.cmd.quit()
    return dump_rep_server(pdb_name, frequency_array, id_ptm_idx_dict, regex_color_dict, background_color)


def pdb_file_reader(pdb_file):
    """
    reads a pdb file into protein sequence
    :param pdb_file:
    :return:
    """
    aa_dict = {'ALA': 'A',
               'ARG': 'R',
               'ASN': 'N',
               'ASP': 'D',
               'ASX': 'B',
               'CYS': 'C',
               'GLU': 'E',
               'GLN': 'Q',
               'GLX': 'Z',
               'GLY': 'G',
               'HIS': 'H',
               'ILE': 'I',
               'LEU': 'L',
               'LYS': 'K',
               'MET': 'M',
               'PHE': 'F',
               'PRO': 'P',
               'SER': 'S',
               'THR': 'T',
               'TRP': 'W',
               'TYR': 'Y',
               'VAL': 'V'}

    aa_reg_str = '|'.join([key for key in aa_dict])

    import re

    with open(pdb_file, 'r') as f_o:
        f_split = f_o.read().split('\nATOM')[1:]
        aa_list = [re.search(aa_reg_str, each).group(0) for each in f_split]
        aa_list = [aa_dict[each] for each in aa_list]
    protein_seq = ''
    for i in range(len(aa_list) - 1):
        if aa_list[i + 1] == aa_list[i]:
            continue
        else:
            protein_seq += aa_list[i]
    # add last aa
    protein_seq += aa_list[-1]
    return protein_seq

if __name__ == "__main__":
    ret = show_cov_3d_v2('Q99JR5',
                       'xxx',
                       "C:\\Users\\Chris\\Downloads\\protein-vis\\Protein-Vis\\pdbs\\UP000000589_10090_MOUSE\\AF-Q99JR5-F1-model_v1.pdb",
                       None,
                       None,
                       regex_color_dict=None,
                       png_sava_path=None,
                       base_path=None,
                       background_color='black')


