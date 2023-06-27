import time
import os
import logging
import sqlite3
import uuid
import threading
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import JobModel
from database import Job, Access, Base
from processing import worker

load_dotenv()  # load environmental variables from .env

app = FastAPI(
    title="scvAPI",
    description="API for the SCV web application.",
    version="0.1.0",
)  # create FastAPI instance

logger = logging.getLogger("uvicorn")  # create logger

engine = create_engine(os.getenv('DATABASE_URL'))  # create SQLAlchemy engine

Base.metadata.create_all(engine)  # create database tables

Session = sessionmaker(bind=engine)  # create session factory

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
async def submit_job(job: JobModel, request: Request):
    logger.debug(f"Received job: {job}")
    new_job = Job.from_model(job)  # convert JobModel to Job
    access = Access(
        ip=request.client.host,
        path=request.url.path,
        method=request.method
    )  # store request as access
    session = Session()
    session.add(new_job)
    session.add(access)
    session.commit()

    job_number = new_job.job_number # get job number

    session.close()


    # Start worker thread
    t = threading.Thread(target=worker, args=(job_number, Session(),))
    t.start()

    return {"job_number": job_number}


@app.post("/protein-list")
async def get_protein_list(job_number: str = Form(None)):
    session = Session()
    job = session.query(Job).filter(Job.job_number == job_number).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    seq_results = job.sequence_coverage_results

    return seq_results
