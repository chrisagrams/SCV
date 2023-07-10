import json
import time
import os
import logging
import sqlite3
import uuid
import threading
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from starlette.staticfiles import StaticFiles
from typing import Optional, Union

from models import JobModel, UploadedPDBModel
from database import Job, Access, Base, ProteinStructure, UploadedPDB
from processing import worker
from rendering import get_annotations
from helpers import pymol_view_dict_to_str, pymol_obj_dict_to_str, color_dict_to_str

load_dotenv()  # load environmental variables from .env

app = FastAPI(
    title="scvAPI",
    description="API for the SCV web application.",
    version="0.1.0",
)  # create FastAPI instance

if os.getenv('ENVIRONMENT') == 'development':
    app.mount("/static", StaticFiles(directory="../static"), name="static")  # for development only
    app.mount("/js", StaticFiles(directory="../vendor/js"), name="js")  # for development only

logger = logging.getLogger("uvicorn")  # create logger

engine = create_engine(os.getenv('DATABASE_URL'))  # create SQLAlchemy engine
engine_readonly = create_engine(os.getenv('DATABASE_URL') + "?mode=ro")  # create SQLAlchemy engine for readonly access

Base.metadata.create_all(engine)  # create database tables

SessionLocal = sessionmaker(bind=engine)  # create session factory
SessionLocalReadonly = sessionmaker(bind=engine_readonly)  # create session factory for readonly access

# Add CORS middleware to allow requests from any origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/test")
async def echo(job: str = Form(None)):
    """
    Basic test to ensure API is responding to requests. Echoes back the job ID that was sent in the request.
    :param job: job ID    :return:
    """
    logger.info(f"/test received job ID: {job}")
    return {"job": job}


@app.post("/job")
async def submit_job(request: Request, job: str = Form(...), file: Optional[UploadFile] = None):
    logger.debug(f"Received job: {job}")

    job_dict = json.loads(job) # convert JSON string to dictionary

    job_data = JobModel(**job_dict) # convert dictionary to JobModel

    new_job = Job.from_model(job_data)  # convert JobModel to Job
    access = Access(
        ip=request.client.host,
        path=request.url.path,
        method=request.method
    )  # store request as access

    pdb_file = None

    if file:
        logger.debug(f"Received file: {file.filename}")
        pdb_upload = UploadedPDBModel(
            pdb_file=file.file.read(),
            filesize=file.file._file.tell(),
            filename=file.filename,
            pdb_id=file.filename.split("-")[1])

        # store PDB file in database
        pdb_file = UploadedPDB.from_model(pdb_upload)

    with SessionLocal() as session:
        session.add(new_job)
        # session.add(access)
        session.commit()

        job_number = new_job.job_number  # get job number

        if pdb_file:
            pdb_file.job_number = job_number
            session.add(pdb_file)
            session.commit()

            # Update job pdb_id
            new_job.pdb_id = pdb_file.pdb_id

        # Start worker thread
        t = threading.Thread(target=worker, args=(job_number, SessionLocal(),))
        t.start()

        return {"job_number": job_number}


@app.post("/job_details")
async def get_job_details(job_number: str = Form(None)):
    with SessionLocalReadonly() as session:
        job = session.query(Job).filter(Job.job_number == job_number).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        return job


@app.post("/protein-list")
async def get_protein_list(job_number: str = Form(None)):
    with SessionLocalReadonly() as session:
        job = session.query(Job).filter(Job.job_number == job_number).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        seq_results = job.sequence_coverage_results

        for seq_result in seq_results:
            structure = session.query(ProteinStructure).filter(
                and_(ProteinStructure.protein_id == seq_result.protein_id,
                     ProteinStructure.species == job.species)).first()
            if structure is None:
                seq_result.has_pdb = False
            else:
                seq_result.has_pdb = True

        return seq_results


@app.post("/protein-structure")
async def get_protein_structure(job_number: str = Form(None), protein_id: str = Form(None)):
    with SessionLocalReadonly() as session:
        job = session.query(Job).filter(Job.job_number == job_number).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        seq_results = job.sequence_coverage_results

        for seq_result in seq_results:
            if seq_result.protein_id == protein_id:
                structure = session.query(ProteinStructure).filter(and_(ProteinStructure.protein_id == protein_id,
                                                                        ProteinStructure.species == job.species)).first()
                if structure is None:
                    raise HTTPException(status_code=404, detail="Protein structure not found")

                annotations = get_annotations(seq_result.sequence_coverage, seq_result.ptms, job.ptm_annotations,
                                              structure.amino_ele_pos)

                ret = pymol_obj_dict_to_str(structure.objs) + \
                      color_dict_to_str(annotations) + \
                      pymol_view_dict_to_str(structure.view) + \
                      f"bgcolor:{job.background_color}"

                return {
                    # "view": structure.view,
                    # "objs": structure.objs,
                    # "annotations": annotations,
                    "pdb_str": structure.pdb_str,
                    "ret": ret
                }

    raise HTTPException(status_code=404, detail="Protein structure not found")
