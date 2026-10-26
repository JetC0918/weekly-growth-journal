from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.store import JournalStore


def test_openapi_is_available_with_an_empty_store():
    client = TestClient(create_app(store=JournalStore()))

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Weekly Growth Journal API"
