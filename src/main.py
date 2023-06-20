import os
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # load environmental variables from .env

app = FastAPI()  # create FastAPI instance


# app.mount("/", StaticFiles(directory="./static"), name="static")


class scvDB:
    _db = None

    @classmethod
    def get_connection(cls):
        if cls._db is None:
            cls._db = sqlite3.connect(os.getenv('DB_PATH'))
        return cls._db


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


@app.post("/protein-list")
async def get_protein_list(job: str = Form(None)):
    db = scvDB.get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM results WHERE job_number = ?", (job,))
    row = cursor.fetchone()
    cursor.close()

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
