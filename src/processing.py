from collections import defaultdict
import time
from heapq import heappush, heappop
import re
import numpy as np
import ahocorasick


def generate_peptide_psm_dict(psm_dict, regex_dict):
    peptide_psm_dict = defaultdict(list)
    invalid_keys = []

    if regex_dict:
        for key in psm_dict:
            if key != 'unlabeled' and key not in regex_dict:
                peptide_psm_dict[key].extend(psm_dict[key])
                invalid_keys.append(key)

        for key in invalid_keys:
            del psm_dict[key]
        if 'unlabeled' not in psm_dict: # if unlabeled is not in psm_dict, add it
            psm_dict['unlabeled'] = []
        psm_dict['unlabeled'].extend(peptide_psm_dict[key])

    return psm_dict, peptide_psm_dict


def generate_psm_group_dict(psm_dict: object) -> object:
    return {psm: group for group in psm_dict if group != "unlabeled" for psm in psm_dict[group]}


def process_psm_list(psm_list, regex_pat, my_replace, peptide_psm_dict):
    for psm in psm_list:
        psm_reg_sub = re.sub(regex_pat, my_replace, psm)
        peptide_psm_dict[psm_reg_sub].append(psm)

    return peptide_psm_dict


def my_replace(match_obj):
    match_obj = match_obj.group()
    return match_obj[0]  # gives back the first element of matched object as string


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


def fasta_reader(fasta_path: str):
    protein_dict = {}
    with open(fasta_path, 'r') as f_o:
        file_split = f_o.read().split('\n>')

    for each in file_split:
        first_line, seq = each.split('\n')[0], ''.join(each.split('\n')[1:])
        uniprot_id = first_line.split('|')[1]
        gene = first_line.split('GN=')[1].split(' ')[0] if 'GN=' in first_line else 'N/A'
        des = ' '.join(first_line.split(' ')[1:]).split(' OS=')[0]
        protein_dict[uniprot_id] = (seq, gene, des)
    return protein_dict


def extract_UNID_and_seq(protein_dict):
    UNID_list = [key for key in protein_dict.keys()]
    seq_list = [value[0] for value in protein_dict.values()]
    return UNID_list, seq_list


def zero_line_for_seq(seq_line):
    zero_line = np.zeros(len(seq_line), dtype=np.int32)
    return zero_line


def separator_pos(seq_line):
    """
    Return the position of each separator in the sequence line
    :param seq_line:
    :return: An array of separator positions
    """
    sep_pos_array = np.array([m.start() for m in re.finditer('\|', seq_line)], dtype=np.int32)
    sep_pos_array = np.insert(sep_pos_array, 0, 0)
    sep_pos_array = np.append(sep_pos_array, len(seq_line))
    return sep_pos_array


def process_aho_result(aho_result, ptm_index_line_dict, peptide_psm_dict, psm_group_dict, zero_line):
    for tp in aho_result:
        matched_pep = tp[2]  # without ptm site
        zero_line[tp[0]:tp[1] + 1] += len(peptide_psm_dict[matched_pep])

        # ptm assign might need to be optimized
        if ptm_index_line_dict:  # if ptm enabled
            for psm in peptide_psm_dict[matched_pep]:
                # first label group PTM
                if psm in psm_group_dict:
                    group_ptm = psm_group_dict[psm]
                    ptm_index_line_dict[group_ptm][tp[0]:tp[1] + 1] += 1

                # then label each PTM inside each PSM
                for ptm in ptm_index_line_dict:
                    # Create a pattern for regex operation
                    ptm_pattern = re.escape(ptm)

                    # Find all occurrences of ptm in psm
                    ptm_occurrences = [m.start() for m in re.finditer(ptm_pattern, psm)]

                    # Adjust the index for occurrences
                    adjusted_occurrences = [ind - i * (len(ptm) - 1) for i, ind in enumerate(ptm_occurrences)]

                    # Increment the count in ptm_index_line_dict
                    for indx in adjusted_occurrences:
                        ptm_index_line_dict[ptm][tp[0] + indx] += 1
    return zero_line, ptm_index_line_dict


def calculate_coverage(zero_line_slice):
    '''
    Calculate the coverage of a slice by counting the number of non-zero elements
    :param zero_line_slice:
    :return:
    '''
    length = len(zero_line_slice)
    if length > 0 and np.any(zero_line_slice):
        percentage_cov = np.count_nonzero(zero_line_slice) / length
    else:
        percentage_cov = 0.0
    return percentage_cov


def calculate_coverage_and_ptm(sep_pos_array, id_list, zero_line, protein_dict, pdbs, ptm_index_line_dict,
                               regex_dict):
    id_freq_array_dict = {}
    id_ptm_idx_dict = {}
    h = []

    start_time = time.time()

    for i in range(len(sep_pos_array) - 1):
        zero_line_slice = zero_line[sep_pos_array[i] + 1:sep_pos_array[i + 1]]
        percentage_cov = calculate_coverage(zero_line_slice)
        if percentage_cov != 0.0:  # only add if the coverage is not 0
            heappush(h, (percentage_cov, (id_list[i], protein_dict[id_list[i]]), zero_line_slice.tolist(),
                         id_list[i] in pdbs))

            id_freq_array_dict[id_list[i]] = zero_line_slice.tolist()  # add the freq array to the dict

            if regex_dict and ptm_index_line_dict:  # if ptm enabled
                for ptm in ptm_index_line_dict:  # for each ptm
                    idx_list = \
                        np.array(np.nonzero(ptm_index_line_dict[ptm][sep_pos_array[i] + 1:sep_pos_array[i + 1]]))[
                            0].tolist()
                    if len(idx_list) > 0:  # only add if there is ptm
                        if id_list[i] not in id_ptm_idx_dict:
                            id_ptm_idx_dict[id_list[i]] = {}
                        id_ptm_idx_dict[id_list[i]].update({ptm: idx_list})

    print('Time used for calculating coverage and ptm: ', time.time() - start_time)

    return id_freq_array_dict, id_ptm_idx_dict, [heappop(h) for i in range(len(h))][::-1]


def freq_ptm_index_gen_batch(psms, ptm_annotations, protein_dict, pdbs):
    id_freq_array_dict = {}
    id_ptm_idx_dict = {}
    h = []
    regex_pat = '\w{1}\[\d+\.?\d+\]'  # universal ptm pattern

    psm_dict, peptide_psm_dict = generate_peptide_psm_dict(psms, ptm_annotations)
    psm_group_dict = generate_psm_group_dict(psm_dict)  # maps psm to group
    psm_list = set([psm for v in psm_dict.values() for psm in v])
    peptide_psm_dict = process_psm_list(psm_list, regex_pat, my_replace, peptide_psm_dict)

    # aho mapping
    id_list, seq_list = extract_UNID_and_seq(protein_dict)
    seq_line = '|'.join(seq_list)
    zero_line = zero_line_for_seq(seq_line)

    ptm_index_line_dict = {each: zero_line_for_seq(seq_line) for each in ptm_annotations} if ptm_annotations else False

    sep_pos_array = separator_pos(seq_line)
    aho_result = automaton_matching(automaton_trie([pep for pep in peptide_psm_dict]), seq_line)

    zero_line, ptm_index_line_dict = process_aho_result(aho_result, ptm_index_line_dict, peptide_psm_dict,
                                                        psm_group_dict, zero_line)

    id_freq_array_dict, id_ptm_idx_dict, heap_array = calculate_coverage_and_ptm(
        sep_pos_array, id_list, zero_line, protein_dict, pdbs, ptm_index_line_dict, ptm_annotations)

    return id_freq_array_dict, id_ptm_idx_dict, heap_array


if __name__ == "__main__":
    fasta_file = "C:\\Users\\Chris\\Downloads\\protein-vis\\Protein-Vis\\fastas\\uniprot-proteome_UP000000589_sp_only_mouse.fasta"
    psm_dict = {
        "unlabeled": [
            "GRADECALPYLGATCYCDLFCN[115]R",
            "GTNECDIETFVLGVWGR",
            "EQNEASPTPR",
            "GNYGWQAGN[115]HSAFWGMTLDEGIR",
            "CPNGQVDSNDIYQVTPAYR",
            "DLSWQVRSLLLDHNR",
            "CNCALRPLCTWLR",
            "RPGSRNRPGYGTGYF",
            "RPDGDAASQPRTPILLLR",
            "QSLRQELYVQDYASIDWPAQR",
            "GTNGSQIWDTSFAIQALLEAGAHHR",
            "ETLNQGLDFCRRKQR",
            "SYFTDLPKAQTAHEGALN[115]GVTFYAK",
            "CDGEANVFSDLHSLRQFTSR",
            "ETFHGLKELAFSYLVWDSK",
            "IKNIYVSDVLNMK"
        ],
        "group1": [
            "EQNEASPTPR",
            "YCQEQDMCCR",
            "ELAPGLHLR",
            "GVVSDNCYPFSGR",
            "C[143]TCHEGGHWECDQEPCLVDPDMIK"
        ]
    }
    # psm_dict = \
    #     {"group1": ["C[143]TCHEGGHWECDQEPCLVDPDMIK", "GRADECALPYLGATCYCDLFCN[115]R"]}

    ptm_annotations = {"C[143]": [255, 0, 247], "N[115]": [0, 255, 8]}
    # psm_dict = {
    #     "group1": ['MGWAGDAGCTPRPPIRPRPASERRVIIVLFLGLLLDLLAFTLLLPLLPGLLERHGREQDP',
    #                'LYGSWQRGVDWFASAIGMPAEKRYNSVLFGGLIGSAFSLLQFFSAPLTGAASDYLGRRPV'],
    #     "unlabeled": ['MMLSLTGLAISYAVWATSRSFKAFLASRVIGGISKGNVNLSTAIVADLGSPPTRSQGMAV']
    # }
    # ptm_annotations = {'group1': [255, 0, 0], "C[143]": [0,255,0], "N[115]": [0,255,255], "unlabeled": [0, 0, 0]}
    pdbs = {'AF-Q9D2V8-F1-model_v1.pdb', 'AF-Q8BLN5-F1-model_v1.pdb'}  # currently a set of pdbs, will connect to database later

    start_time = time.time()
    protein_dict = fasta_reader(fasta_file)
    print('Time used for reading fasta: ', time.time() - start_time)

    start_time = time.time()
    id_freq_array_dict, id_ptm_idx_dict, heap_array = freq_ptm_index_gen_batch(psm_dict, ptm_annotations, protein_dict,
                                                                               pdbs)
    print('Time used for generating freq and ptm index: ', time.time() - start_time)
    print(id_freq_array_dict)
    print(id_ptm_idx_dict)
    print(heap_array)
