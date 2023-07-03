import os
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, ProteinStructure
from src.rendering import get_db_model_from_pdb

load_dotenv('../.env')  # load environmental variables from .env

engine = create_engine(os.getenv('DATABASE_URL'))  # create SQLAlchemy engine

Base.metadata.create_all(engine)  # create database tables

Session = sessionmaker(bind=engine)  # create session factory


def main():
    parser = argparse.ArgumentParser(description="Process PDB files into database.")
    parser.add_argument('-d', '--directory', help="Directory of PDB files", required=True)
    parser.add_argument('-s', '--species', help="Desired species.", required=True)
    parser.add_argument('--database', help="Database to add to.", default=os.getenv('DATABASE_URL'), required=False)

    args = parser.parse_args()

    session = Session()
    # existing_entry = session.query(ProteinStructure).filter_by(name=args.name).first()
    # if existing_entry:
    #     print(f"Entry with name \"{args.name}\" already exists in database.")
    #     return

    # Get all PDB files in directory
    pdb_files = [os.path.join(args.directory, f) for f in os.listdir(args.directory) if f.endswith('.pdb')]
    if len(pdb_files) == 0:
        print(f"No PDB files found in {args.directory}.")
        return

    # Render 3D Structures
    for pdb_file in tqdm(pdb_files, desc="Processing files", unit="file"):
        mdl = get_db_model_from_pdb(pdb_file, os.path.basename(pdb_file), os.path.basename(pdb_file).split('-')[1], args.species)

        # Check if entry already exists
        existing_entry = session.query(ProteinStructure).filter_by(id=mdl.id).first()
        if existing_entry:
            print(f"Entry with id \"{mdl.id}\" already exists in database.")
            continue
        else:
            session.add(mdl)
            session.commit()
            print(f"Added {pdb_file} to database as \"{mdl.id}.\"")

    session.close()


if __name__ == "__main__":
    main()
