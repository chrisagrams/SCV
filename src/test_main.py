import json

import pytest
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_echo():
    """
    Basic test to ensure API is responding to requests. Echoes back the job ID that was sent in the request.

    This function generates a unique identifier (UUID) for the test job and sends a POST request to the "/test" endpoint
    with the generated job ID. It then asserts that the response status code is 200 (OK) and that the response JSON
    matches the expected result, which is a dictionary with the "job" key equal to the generated job ID.
    """
    test_uuid = str(uuid.uuid4())
    response = client.post("/test", data={"job": test_uuid})
    assert response.status_code == 200
    assert response.json() == {"job": test_uuid}


# def test_get_protein_list():
#     response = client.post("/protein-list", data={"job": "1"})
#     assert response.status_code == 200
#     assert response.json() == {
#         "job_number": "1",
#         "pq": "1",
#         "id_ptm_idx_dict": "1",
#         "regex_dict": "1",
#         "background_color": "1",
#         "pdb_dest": "1"
#     }

def test_empty_submit_job():
    response = client.post("/job",  data=json.dumps(
    {"psms": None,
     "ptm_annotations": None,
     "background_color": None,
     "species": None}), headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    response = client.post("/job", data=json.dumps({}), headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    response = client.post("/job", json.dumps(
    {"psms": {},
     "ptm_annotations": {},
     "background_color": 0,
     "species": ""}), headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_invalid_job_psms():
    response = client.post("/job", data=
        json.dumps({"psms": None,
                     "ptm_annotations": {},
                     "background_color": 0,
                     "species": ""}),
        headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'psms'], 'msg': 'PSMs must be specified.',
                                           'type': 'value_error'}]}
    response = client.post("/job", data=
        json.dumps({"psms": {},
                    "ptm_annotations": {},
                    "background_color": 0,
                    "species": ""}),
        headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'psms'], 'msg': 'PSMs must contain at least one group.',
                                              'type': 'value_error'}]}
    response = client.post("/job", data=
        json.dumps({"psms": {"group1": "ABC"},
                    "ptm_annotations": {},
                    "background_color": 0,
                    "species": ""}),
        headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'psms'],
                                         'msg': 'PSM values must be lists.',
                                         'type': 'value_error'}]}
    response = client.post("/job", data=
        json.dumps({"psms": {"group1": ["ZZZ"]},
                    "ptm_annotations": {},
                    "background_color": 0,
                    "species": ""}),
        headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'psms'], 'msg': 'PSM values must be lists of '
                                                                                        'valid peptide sequences.',
                                              'type': 'value_error'}]}


def test_invalid_job_background_color():
    response = client.post("/job", data=
        json.dumps({"psms": {"group1": ["ABC", "DEF"]},
         "ptm_annotations": {},
         "background_color": -1,
         "species": ""}),
        headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'background_color'], 'msg': 'Background color must be a '
                                                                                       'positive integer.',
                                           'type': 'value_error'}]}


def test_get_invalid_protein_list():
    response = client.post("/protein-list", data={"job": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404
    assert response.json() == {"error": "No matching job number found."}
