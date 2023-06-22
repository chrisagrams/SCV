import time
import os
import logging
import sqlite3
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import JobModel
from database import Job, Access, Base

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
    return {"job_number": new_job.job_number}


@app.post("/protein-list")
async def get_protein_list(job: str = Form(None)):
    return {"protein_list": ["P12345", "P67890"]}
    # db = scvDB.get_connection()
    # if db is None:
    #     raise HTTPException(status_code=500, detail="Internal server error")
    # try:
    #     cursor = db.cursor()
    #     cursor.execute("SELECT * FROM results WHERE job_number = ?", (job,))
    #     row = cursor.fetchone()
    #     cursor.close()
    # except sqlite3.Error as e:
    #     logger.error(e)
    #     raise HTTPException(status_code=500, detail="Internal server error")
    # if row:
    #     result = {
    #         "job_number": row[0],
    #         "pq": row[1],
    #         "id_ptm_idx_dict": row[2],
    #         "regex_dict": row[3],
    #         "background_color": row[4],
    #         "pdb_dest": row[5]
    #     }
    #     return result
    # else:
    #     return {"error": "No matching job number found."}
