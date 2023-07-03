import multiprocessing
import os
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, ProteinStructure
from src.rendering import get_db_model_from_pdb

load_dotenv('../.env')  # load environmental variables from .env

parser = argparse.ArgumentParser(description="Process PDB files into database.")
parser.add_argument('-d', '--directory', help="Directory of PDB files", required=True)
parser.add_argument('-s', '--species', help="Desired species.", required=True)
parser.add_argument('--database', help="Database to add to.", default=os.getenv('DATABASE_URL'), required=False)

args = parser.parse_args()


def process_pdb_file(pdb_file):
    # Create a new session for this process
    engine = create_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(bind=engine)
    session = Session()

    mdl = get_db_model_from_pdb(pdb_file, os.path.basename(pdb_file), os.path.basename(pdb_file).split('-')[1], args.species)

    # Check if entry already exists
    existing_entry = session.query(ProteinStructure).filter_by(id=mdl.id).first()
    if existing_entry:
        session.close()
        return f"Entry with id \"{mdl.id}\" already exists in database."
    else:
        session.merge(mdl) # merge the object into the session
        session.commit()
        session.close()
        return f"Added {pdb_file} to database as \"{mdl.id}.\""


def main():
    # Get all PDB files in directory
    pdb_files = [os.path.join(args.directory, f) for f in os.listdir(args.directory) if f.endswith('.pdb')]
    if len(pdb_files) == 0:
        print(f"No PDB files found in {args.directory}.")
        return

    # Use a multiprocessing Pool
    with multiprocessing.Pool() as pool:
        for message in tqdm(pool.imap_unordered(process_pdb_file, pdb_files), total=len(pdb_files),
                            desc="Processing files", unit="file"):
            print(message)


if __name__ == "__main__":
    main()
