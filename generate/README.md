# Dataset Generation

This directory contains several scripts that are used to generate the required datasets for SCV.
These scripts will add the datasets directly to the SQLite database located under `../database/` (or wherever specified in the .env file).
These scripts can be executed locally. The resulting SQLite database can be attached as a volume to the Docker container.

## Table of Contents
- [Adding FASTA Files](#adding-fasta-files)
- [Other Scripts](#other-scripts)

## Adding FASTA Files

The script `generate_fasta.py` in the `generate/` directory is used to add FASTA files to the SQLite database. 

It takes two command-line arguments:

1. `-f` or `--fasta`: This is the path to the FASTA file you want to add.
2. `-n` or `--name`: This is the name you want to give to the FASTA file in the database.
3. (Optional) `--database`: This is the path to the SQLite database. If not specified, the script will look for the database specified in the .env file.

For example, to add a FASTA file located at `/path/to/fasta/file` with the name "MyFasta", you would use the following command:

```bash
python generate_fasta.py -f /path/to/fasta/file -n "MyFasta"
