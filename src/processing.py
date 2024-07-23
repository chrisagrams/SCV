from collections import defaultdict
import time
import re
import numpy as np
import ahocorasick

from database import Job, SequenceCoverageResult, FASTA_Entry
from models import SequenceCoverageModel
from helpers import fasta_reader, calc_hash_of_dict


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
        if 'unlabeled' not in psm_dict:  # if unlabeled is not in psm_dict, add it
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



def extract_UNID_and_seq(protein_dict):
    UNID_list = [key for key in protein_dict.keys()]
    seq_list = [value['sequence'] for value in protein_dict.values()]
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

                    # FIX: find other ptm positions as well
                    ptm_positions = [m.span() for m in re.finditer(r"\[(.*?)\]", psm)]
                    ptm_end_pos = [i[1] for i in ptm_positions]
                    ptm_len = [i[1] - i[0] for i in ptm_positions]
                    ptm_offset = [sum(ptm_len[:idx + 1]) for idx, value in enumerate(ptm_len)]
                    pos_shift_dict = dict(zip(ptm_end_pos, ptm_offset))
                    ptm_shift_dict= {}
                    current_shift = 0
                    for i in range(len(psm)):
                        if i in pos_shift_dict:
                            current_shift = pos_shift_dict[i]
                        ptm_shift_dict[i] = current_shift

                    # Adjust the index for occurrences
                    adjusted_occurrences = [ind - ptm_shift_dict[ind] for ind in ptm_occurrences]

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
    identified = {}

    start_time = time.time()

    for i in range(len(sep_pos_array) - 1):
        zero_line_slice = zero_line[sep_pos_array[i] + 1:sep_pos_array[i + 1]]
        percentage_cov = calculate_coverage(zero_line_slice)
        if percentage_cov != 0.0:  # only add if the coverage is not 0
            identified[id_list[i]] = {
                'coverage': percentage_cov,
                'protein_id': id_list[i],
                'sequence': protein_dict[id_list[i]]['sequence'],
                'UNID': protein_dict[id_list[i]]['gene'],
                'description': protein_dict[id_list[i]]['des'],
                'sequence_coverage': zero_line_slice.tolist(),
                'has_pdb': id_list[i] in pdbs,
                'ptms': {}  # will be filled later
            }

            if regex_dict and ptm_index_line_dict:  # if ptm enabled
                for ptm in ptm_index_line_dict:  # for each ptm
                    idx_list = \
                        np.array(np.nonzero(ptm_index_line_dict[ptm][sep_pos_array[i] + 1:sep_pos_array[i + 1]]))[
                            0].tolist()
                    identified[id_list[i]]['ptms'].update({ptm: idx_list})

            # Store the sequence coverage hash
            hsh = calc_hash_of_dict(identified)
            identified[id_list[i]]['id'] = hsh

    print('Time used for calculating coverage and ptm: ', time.time() - start_time)

    return identified


def freq_ptm_index_gen_batch(psms, ptm_annotations, protein_dict, pdbs):

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

    identified = calculate_coverage_and_ptm(
        sep_pos_array, id_list, zero_line, protein_dict, pdbs, ptm_index_line_dict, ptm_annotations)

    return identified


def gen_sequence_cov_model(cov_dict):
    """
    Generate a sequence coverage model from a sequence coverage dictionary
    :param cov_dict:
    :return:
    """

    # Create a new sequence coverage model
    seq_cov_model = SequenceCoverageModel()

    # Add the sequence coverage dictionary to the model
    seq_cov_model = seq_cov_model.from_dict(cov_dict)

    # Return the sequence coverage model
    return seq_cov_model


def gen_sequence_cov_models(identified_dict):
    mdls = []
    for key in identified_dict:
        mdl = gen_sequence_cov_model(identified_dict[key])
        mdls.append(mdl)
    return mdls


def worker(job_number, session):

    # Get the job
    job = session.query(Job).filter(Job.job_number == job_number).first()

    # Get protein dictionary
    fasta = session.query(FASTA_Entry).filter(FASTA_Entry.name == job.species).first()
    if fasta is None:
        raise ValueError('No fasta entry found for species: {}'.format(job.species))
    protein_dict = fasta.data

    # Identify sequence coverage
    identified = freq_ptm_index_gen_batch(job.psms, job.ptm_annotations, protein_dict, pdbs={}) # TODO: add pdbs

    # Generate sequence coverage models
    seq_cov_models = gen_sequence_cov_models(identified)

    # Add the sequence coverage models to the database
    for seq_cov_model in seq_cov_models:
        # First check if the sequence coverage model already exists
        seq_cov_res = session.query(SequenceCoverageResult).filter(
            SequenceCoverageResult.id == seq_cov_model.id).first()

        if seq_cov_res is None:
            # If the sequence coverage model does not exist, add it to the database
            seq_cov_res = SequenceCoverageResult.from_model(seq_cov_model)
            session.add(seq_cov_res)

            # Get all jobs with job_number == job_number
            jobs = session.query(Job).filter(Job.job_number == job_number).all()

            # Add the job to the sequence coverage model
            for job in jobs:
                seq_cov_res.jobs.append(job)

        else:
            # If the sequence coverage model does exist, add the job to the sequence coverage model
            seq_cov_res.jobs.append(job)

    # Commit the changes
    session.commit()

    # Close the session
    session.close()



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
    pdbs = {'Q9D2V8',
            'Q8BLN5'}  # currently a set of pdbs, will connect to database later

    start_time = time.time()
    protein_dict = fasta_reader(fasta_file)
    print('Time used for reading fasta: ', time.time() - start_time)

    start_time = time.time()
    identified = freq_ptm_index_gen_batch(psm_dict, ptm_annotations, protein_dict,
                                                                               pdbs)
    print('Time used for generating freq and ptm index: ', time.time() - start_time)
    # print(identified)
    print(gen_sequence_cov_models(identified, job_number='test'))
