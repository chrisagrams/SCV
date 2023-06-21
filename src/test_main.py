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