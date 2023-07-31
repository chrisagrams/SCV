import multiprocessing
import os
import sys
import argparse
import logging
import time

import sqlalchemy
from dotenv import load_dotenv
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(filename="process_pdb_log.txt", format='%(message)s', level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Base, ProteinStructure
from src.rendering import get_db_model_from_pdb

load_dotenv('../.env')  # load environmental variables from .env

parser = argparse.ArgumentParser(description="Process PDB files into database.")
parser.add_argument('-d', '--directory', help="Directory of PDB files", required=True)
parser.add_argument('-s', '--species', help="Desired species.", required=True)
parser.add_argument('--database', help="Database to add to.", default=os.getenv('DATABASE_URL'), required=False)

args = parser.parse_args()

engine = create_engine(os.getenv('DATABASE_URL'))

Base.metadata.create_all(engine)  # create database tables


def process_pdb_file(pdb_file, max_retries=5, wait_time=5):
    # Create a new session for this process
    engine = create_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(bind=engine)

    for attempt in range(
            max_retries):  # try max_retries times, wait for wait_time seconds between each attempt to reduce contention
        try:
            session = Session()

            mdl = get_db_model_from_pdb(pdb_file, os.path.basename(pdb_file), os.path.basename(pdb_file).split('-')[1],
                                        args.species)

            # Check if entry already exists
            existing_entry = session.query(ProteinStructure).filter_by(id=mdl.id).first()
            if existing_entry:
                session.close()
                return f"Entry with id \"{mdl.id}\" already exists in database."
            else:
                session.merge(mdl)  # merge the object into the session
                session.commit()
                session.close()
                return f"Added {pdb_file} to database as \"{mdl.id}.\""
        except sqlalchemy.exc.OperationalError as e:
            if "database is locked" in str(
                    e) and attempt < max_retries - 1:  # check if it's a locked error and if we haven't exceeded max_retries
                time.sleep(wait_time)  # wait before retrying
                continue
            else:
                raise  # if it's a different OperationalError, or we've exceeded max_retries, raise the exception


def main():
    # Get all PDB files in directory
    pdb_files = [os.path.join(args.directory, f) for f in os.listdir(args.directory) if f.endswith('.pdb')]
    if len(pdb_files) == 0:
        print(f"No PDB files found in {args.directory}.")
        return

    # Use a multiprocessing Pool
    with multiprocessing.Pool() as pool:
        with tqdm(total=len(pdb_files), desc="Processing files", unit="file") as pbar:
            for message in pool.imap_unordered(process_pdb_file, pdb_files):
                logging.info(message)
                pbar.update()  # manually update the progress bar


if __name__ == "__main__":
    main()
