"""Module responsible for testing backend functionalities."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Adjust the Python path to include the src directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.app import app

CORRECT_RESPONSE_STATUS_CODE = 200

@pytest.fixture()
def client() -> TestClient:
    """TestClient fixture for FastAPI app."""
    return TestClient(app)

def test_query_endpoint(client : TestClient) -> None:
    """Test the query endpoint locally."""
    response = client.post("/query", json={"query": "test",
                                           "model_name" : "gemma-7b-it" },
                                           timeout=30)
    assert response.status_code == CORRECT_RESPONSE_STATUS_CODE
    assert "answer" in response.json()
    assert "documents" in response.json()


def test_feedback_endpoint(client : TestClient) -> None:
    """Test the feedback endpoint locally."""
    response = client.post("/feedback", json={"query": "test",
                                              "feedback" : "test" },
                                              timeout=30)
    assert response.status_code == CORRECT_RESPONSE_STATUS_CODE
    assert "message" in response.json()
    assert response.json()["message"] == "Feedback received"
