def fasta_reader(fasta_path: str):
    protein_dict = {}
    with open(fasta_path, 'r') as f_o:
        file_split = f_o.read().split('\n>')

    for each in file_split:
        first_line, seq = each.split('\n')[0], ''.join(each.split('\n')[1:])
        uniprot_id = first_line.split('|')[1]
        gene = first_line.split('GN=')[1].split(' ')[0] if 'GN=' in first_line else 'N/A'
        des = ' '.join(first_line.split(' ')[1:]).split(' OS=')[0]
        protein_dict[uniprot_id] = {'sequence': seq, 'gene': gene, 'des': des}
    return protein_dict
