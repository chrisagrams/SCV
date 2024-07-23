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


def test_empty_submit_job():
    response = client.post("/job", data={"psms": "",
                                         "ptm_annotations": "",
                                         "background_color": "",
                                         "species": ""}, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    response = client.post("/job", data={}, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    response = client.post("/job", data={
        "psms": {},
        "ptm_annotations": {},
        "background_color": 0,
        "species": ""}, headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_invalid_job_psms():
    response = client.post("/job", data={
        "psms": "",
        "ptm_annotations": {},
        "background_color": 0,
        "species": ""},
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'value_error.missing'
    response = client.post("/job", data={
        "psms": {},
        "ptm_annotations": {},
        "background_color": 0,
        "species": ""},
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'value_error.missing'
    response = client.post("/job", data={
        "psms": {"group1": "ABC"},
        "ptm_annotations": {},
        "background_color": 0,
        "species": ""},
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'value_error.missing'
    response = client.post("/job", data={
        "psms": {"group1": ["ZZZ"]},
        "ptm_annotations": {},
        "background_color": 0,
        "species": ""},
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'value_error.missing'


def test_invalid_job_background_color():
    response = client.post("/job", data={
        "psms": {"group1": ["ABC", "DEF"]},
        "ptm_annotations": {},
        "background_color": -1,
        "species": ""},
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json() is not None
    assert response.json()['detail'][0]['type'] == 'value_error.missing'


def test_get_invalid_protein_list():
    response = client.post("/protein-list", data={"job": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}
