import configparser
import json
import os
import logging
import threading
import pydantic
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, joinedload
from starlette.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional
from configparser import ConfigParser

from src.models import JobModel, UploadedPDBModel, SequenceCoverageModel
from src.database import Job, Access, Base, ProteinStructure, UploadedPDB, SequenceCoverageResult, USI
from src.processing import worker
from src.rendering import get_annotations
from src.helpers import pymol_view_dict_to_str, pymol_obj_dict_to_str, color_dict_to_str, calc_hash_of_dict

load_dotenv('.env')  # load environmental variables from .env

log_config = ConfigParser()  # load logging configuration
log_config.read('./logging.ini')

app = FastAPI(
    title="scvAPI",
    description="API for the SCV web application.",
    version="1.2.0",
)  # create FastAPI instance

limiter = Limiter(key_func=get_remote_address)  # create rate limiter
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if os.getenv('ENVIRONMENT') == 'development':
    app.mount("/html", StaticFiles(directory="./static/html"), name="html")  # for development only
    app.mount("/css", StaticFiles(directory="./static/css"), name="css")  # for development only
    app.mount("/js", StaticFiles(directory="./static/js"), name="js")  # for development only
    app.mount("/vendor/js", StaticFiles(directory="./vendor/js"), name="js")  # for development only

# === Configure logger === #

logger = logging.getLogger("uvicorn")  # create logger
try:
    log_level = log_config.get("Logging", "LogLevel")
except configparser.NoSectionError or configparser.NoOptionError:
    logger.warning("Could not find LogLevel in logging.ini, defaulting to INFO")
    log_level = "INFO"
numeric_level = getattr(logging, log_level.upper(), logging.INFO)
logger.setLevel(numeric_level)

# Disable propagation of log entries from Uvicorn logger to parent loggers
logger.propagate = False

# Create a console handler and set the log level
console_handler = logging.StreamHandler()
console_handler.setLevel(numeric_level)

try:  # try to get log file path from logging.ini
    log_file = log_config.get("Logging", "LogFile")
except configparser.NoSectionError or configparser.NoOptionError:
    logger.warning("Could not find LogFile in logging.ini, defaulting to scv.log")
    log_file = "scv.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(numeric_level)

# Create a formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
    logger.addHandler(console_handler)
logger.addHandler(file_handler)

# === Configure database === #

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


def load_limiter_config():
    """
    Loads rate limiter configuration from rates.json.
    """
    try:
        with open("./rates.json") as f:
            limiter_config = json.load(f)
            for endpoint, rate_limit in limiter_config.items():
                limiter.limit(rate_limit, key_func=lambda _: endpoint)
    except FileNotFoundError:
        logger.warning("Could not find rates.json, no rate limiting will be applied.")


@app.on_event("startup")
async def startup_event():
    """
    Runs on app startup.
    Loads rate limiter configuration and applies it to the API.
    :return:
    """
    load_limiter_config()
    logger.info("=== New instance started ===")


# === Endpoint definitions ===


@app.post("/test")
async def echo(request: Request, job: str = Form(None)):
    """
    Basic test to ensure API is responding to requests. Echoes back the job ID that was sent in the request.
    """
    logger.info(f"/test received job ID: {job}")
    try:
        access = Access(ip=request.client.host, path=request.url.path, method=request.method)
        with SessionLocal() as session:
            session.add(access)
            session.commit()
    except SQLAlchemyError as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Database error")
    return {"job": job}


@app.post("/job")
async def submit_job(request: Request, job: str = Form(...), file: Optional[UploadFile] = None):
    """
    Endpoint for submitting a job to the API. Accepts a JSON string containing the job data, and an optional PDB file.
    Starts a worker thread to process the job.
    """
    try:
        logger.debug(f"Received job: {job}")

        job_dict = json.loads(job)  # convert JSON string to dictionary

        job_data = JobModel(**job_dict)  # convert dictionary to JobModel

        new_job = Job.from_model(job_data)  # convert JobModel to Job

        access = Access(ip=request.client.host, path=request.url.path, method=request.method)  # store request as access

        pdb_file = None

        if file:  # if a file was uploaded, store it in the database
            logger.debug(f"Received file: {file.filename}")
            if not file.filename.endswith(".pdb"):
                raise HTTPException(status_code=400, detail="Uploaded file must be a PDB file.")
            pdb_upload = UploadedPDBModel(
                pdb_file=file.file.read(),
                filesize=file.file._file.tell(),
                filename=file.filename,
                pdb_id=file.filename.split("-")[1])

            # store PDB file in database
            pdb_file = UploadedPDB.from_model(pdb_upload)

        with SessionLocal() as session:  # create session, locks database!
            session.add(new_job)  # add job to db
            session.commit()  # commit job to db

            job_number = new_job.job_number  # get job number

            access.job_number = job_number  # add job number to access
            session.add(access)  # add access to db

            if pdb_file:
                pdb_file.job_number = job_number
                session.add(pdb_file)

                # Update job pdb_id
                new_job.pdb_id = pdb_file.pdb_id

            session.commit()  # commit access and pdb file to db

        # Start worker thread, pass session factory to worker
        t = threading.Thread(target=worker, args=(job_number, SessionLocal(),))
        t.start()

        return {"job_number": job_number}

    except json.JSONDecodeError:  # if JSON is invalid
        raise HTTPException(status_code=400, detail=[{"type": "decode_error", "msg": "Invalid JSON"}])
    except pydantic.ValidationError as ve:  # if JobModel or UploadedPDBModel is invalid
        raise HTTPException(status_code=400, detail=json.loads(ve.json()))
    except threading.ThreadError as te:
        raise HTTPException(status_code=500, detail="Internal error.")
    except SQLAlchemyError as se:
        raise HTTPException(status_code=500, detail="Internal error.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error.")


@app.post("/job_details")
async def get_job_details(request: Request, job_number: str = Form(None)):
    try:
        access = Access(ip=request.client.host, path=request.url.path, method=request.method, job_number=job_number)
        with SessionLocal() as session:
            session.add(access)
            session.commit()

        with SessionLocalReadonly() as session:
            # job = session.query(Job).filter(Job.job_number == job_number).first()
            job = session.query(Job).options(joinedload(Job.usis)).filter(Job.job_number == job_number).first()
            if job is None:
                raise HTTPException(status_code=404, detail="Job not found")
            return job

    except SQLAlchemyError as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/protein-list")
async def get_protein_list(request: Request, job_number: str = Form(None)):
    try:
        access = Access(ip=request.client.host, path=request.url.path, method=request.method, job_number=job_number)
        with SessionLocal() as session:
            session.add(access)
            session.commit()
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
    except SQLAlchemyError as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/protein-structure")
async def get_protein_structure(request: Request, job_number: str = Form(None), protein_id: str = Form(None)):
    try:
        access = Access(ip=request.client.host, path=request.url.path, method=request.method, job_number=job_number)
        with SessionLocal() as session:
            session.add(access)
            session.commit()
        with SessionLocalReadonly() as session:
            job = session.query(Job).filter(Job.job_number == job_number).first()
            if protein_id is None:
                raise HTTPException(status_code=404, detail="Protein structure not found")
            if job_number is None:
                structure = session.query(ProteinStructure).filter(protein_id == protein_id).first()
                return structure

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
    except SQLAlchemyError as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/external-job")
async def external_job(request: Request,
                       sequence_model: SequenceCoverageModel,
                       job_model: JobModel):
    try:
        if sequence_model is None:
            raise HTTPException(status_code=500, detail="Sequence model not provided")
        if job_model is None:
            raise HTTPException(status_code=500, detail="Job model not provided")

        new_job = Job.from_model(job_model)

        with SessionLocal() as session:  # create session, locks database!
            session.add(new_job)  # add job to db
            session.commit()  # commit job to db

            job_number = new_job.job_number

            # Convert to dict so that we can make a hash using calc_hash_of_dict()
            seq_dict = SequenceCoverageModel.to_dict(sequence_model)
            sequence_model.id = calc_hash_of_dict(seq_dict)

            # Check if hash exists. If it does, don't make a new model.
            seq_cov_res = session.query(SequenceCoverageResult).filter(
                SequenceCoverageResult.id == sequence_model.id).first()

            if seq_cov_res is None:
                new_sequence_coverage = SequenceCoverageResult.from_model(sequence_model)
                new_job.sequence_coverage = new_sequence_coverage
                new_sequence_coverage.jobs.append(new_job)
                session.add(new_sequence_coverage)
            else:
                seq_cov_res.jobs.append(new_job)

            if job_model.usis:
                for usi_data in job_model.usis:
                    usi_instance = USI(**usi_data.dict())
                    usi_instance.jobs.append(new_job)
                    new_job.usis.append(usi_instance)
                    session.add(usi_instance)

            session.commit()

        return {"job_number": job_number}

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404)
