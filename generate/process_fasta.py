import os
import argparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, FASTA_Entry
from src.helpers import fasta_reader

load_dotenv('../.env')  # load environmental variables from .env

engine = create_engine(os.getenv('DATABASE_URL'))  # create SQLAlchemy engine

Base.metadata.create_all(engine)  # create database tables

Session = sessionmaker(bind=engine)  # create session factory


def main():
    parser = argparse.ArgumentParser(description="Process FASTA files into database.")
    parser.add_argument('-f', '--fasta', help="FASTA file to process.", required=True)
    parser.add_argument('-n', '--name', help="Desired name.", required=True)
    parser.add_argument('--database', help="Database to add to.", default=os.getenv('DATABASE_URL'), required=False)

    args = parser.parse_args()

    session = Session()
    existing_entry = session.query(FASTA_Entry).filter_by(name=args.name).first()
    if existing_entry:
        print(f"Entry with name \"{args.name}\" already exists in database.")
        return

    fasta = fasta_reader(args.fasta)

    fasta_entry = FASTA_Entry(
        name=args.name,
        source_filename=os.path.basename(args.fasta),
        data=fasta
    )

    session.add(fasta_entry)
    session.commit()
    session.close()

    print(f"Added {args.fasta} to database as \"{args.name}.\"")


if __name__ == "__main__":
    main()
