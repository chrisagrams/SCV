import time
import os
import logging
import sqlite3
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from models import JobModel


load_dotenv()  # load environmental variables from .env

app = FastAPI(
    title="scvAPI",
    description="API for the SCV web application.",
    version="0.1.0",
)  # create FastAPI instance

logger = logging.getLogger("uvicorn")  # create logger


class scvDB:
    _db = None

    @classmethod
    def get_connection(cls):
        if cls._db is None:
            try:
                db_path = os.getenv('DB_PATH')
                if not os.path.exists(db_path):
                    cls._create_database(db_path)
                cls._db = sqlite3.connect(db_path)
            except sqlite3.Error as e:
                logger.error(e)
                return None
        return cls._db

    @classmethod
    def _create_database(cls, db_path):
        conn = sqlite3.connect(db_path)
        cls._create_access_table(conn)

    @classmethod
    def _create_access_table(cls, conn):
        cursor = conn.cursor()
        # Create the "access" table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access (
                ip TEXT,
                timestamp TEXT,
                path TEXT
            )
        ''')
        conn.commit()

    @classmethod
    def add_access(cls, ip, timestamp, path):
        db = cls.get_connection()
        if db is None:
            return
        try:
            cursor = db.cursor()
            cursor.execute("INSERT INTO access VALUES (?, ?, ?)", (ip, timestamp, path))
            db.commit()
            cursor.close()
        except sqlite3.Error as e:
            raise e

@app.on_event("startup")
async def startup_event():
    scvDB.get_connection()


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
    try:
        scvDB.add_access(request.client.host, time.time(), request.url.path)
    except sqlite3.Error as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.debug(f"Received job: {job}")
    return {"job_number": uuid.uuid4()}


@app.post("/protein-list")
async def get_protein_list(job: str = Form(None)):
    db = scvDB.get_connection()
    if db is None:
        raise HTTPException(status_code=500, detail="Internal server error")
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM results WHERE job_number = ?", (job,))
        row = cursor.fetchone()
        cursor.close()
    except sqlite3.Error as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    if row:
        result = {
            "job_number": row[0],
            "pq": row[1],
            "id_ptm_idx_dict": row[2],
            "regex_dict": row[3],
            "background_color": row[4],
            "pdb_dest": row[5]
        }
        return result
    else:
        return {"error": "No matching job number found."}
