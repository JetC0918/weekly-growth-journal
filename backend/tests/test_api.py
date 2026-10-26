from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.auth import create_access_token
from backend.app.main import create_app
from backend.app.store import create_seeded_store


@pytest.fixture
def client_and_credentials():
    store, username, password = create_seeded_store()
    user = store.user_by_username(username)
    assert user is not None
    client = TestClient(create_app(store))
    token = create_access_token(user.id)
    return client, username, password, token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def review_payload(week_start: date) -> dict:
    return {
        "weekStart": week_start.isoformat(),
        "answers": {
            "wentWell": "I made progress on the first draft.",
            "didntGoWell": "I delayed asking for help.",
            "handledBetter": "I could have asked sooner.",
            "learned": "Small steps help me start.",
            "doDifferently": "I will ask for help on Monday.",
        },
        "freeWriting": "I want to keep building momentum.",
        "followUps": [{"question": "What helped?", "answer": "A short plan."}],
    }


def test_public_registration_and_login_hash_passwords():
    client = TestClient(create_app())
    response = client.post("/api/auth/register", json={"username": "new-user", "password": "a-long-password"})
    assert response.status_code == 201
    token = response.json()["accessToken"]
    assert response.json()["tokenType"] == "bearer"

    user = client.app.state.store.user_by_username("new-user")
    assert user is not None
    assert user.password_hash != "a-long-password"
    assert "$" in user.password_hash
    assert client.post("/api/auth/register", json={"username": "new-user", "password": "a-long-password"}).status_code == 409

    login = client.post("/api/auth/login", json={"username": "new-user", "password": "a-long-password"})
    assert login.status_code == 200
    assert login.json()["accessToken"]
    assert client.post("/api/auth/login", json={"username": "new-user", "password": "incorrect-password"}).status_code == 401
    assert client.get("/api/reviews", headers=auth(token)).status_code == 200


def test_journal_endpoints_require_bearer_and_user_data_is_isolated(client_and_credentials):
    client, _, _, token = client_and_credentials
    assert client.get("/api/reviews").status_code == 401
    assert client.get("/api/reviews", headers=auth("bad-token")).status_code == 401
    assert client.get("/api/reviews", headers=auth(token)).status_code == 200

    register = client.post("/api/auth/register", json={"username": "other", "password": "another-password"})
    other_token = register.json()["accessToken"]
    assert client.get("/api/reviews", headers=auth(other_token)).json() == []


def test_seeded_reviews_and_review_create_update_and_lookup(client_and_credentials):
    client, _, _, token = client_and_credentials
    headers = auth(token)
    seeded = client.get("/api/reviews", headers=headers).json()
    assert len(seeded) >= 2
    assert seeded[0]["weekStart"] > seeded[-1]["weekStart"]

    week = date(2024, 1, 1)
    created = client.post("/api/reviews", json=review_payload(week), headers=headers)
    assert created.status_code == 201
    review = created.json()
    assert review["status"] == "draft"
    assert client.get(f"/api/reviews/{review['id']}", headers=headers).json() == review
    assert client.get(f"/api/reviews/by-week/{week.isoformat()}", headers=headers).json() == review

    updated_payload = review_payload(week)
    updated_payload["freeWriting"] = "Edited reflection."
    updated = client.post("/api/reviews", json=updated_payload, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["id"] == review["id"]
    assert updated.json()["freeWriting"] == "Edited reflection."


def test_followups_complete_report_and_insight_patch(client_and_credentials):
    client, _, _, token = client_and_credentials
    headers = auth(token)
    payload = review_payload(date(2024, 2, 5))
    suggestions = client.post("/api/reviews/suggest-follow-ups", json=payload, headers=headers)
    assert suggestions.status_code == 200
    assert suggestions.json()

    review = client.post("/api/reviews", json=payload, headers=headers).json()
    completion = client.post(f"/api/reviews/{review['id']}/complete", headers=headers)
    assert completion.status_code == 200
    report = completion.json()
    assert report["reviewId"] == review["id"]
    assert client.get(f"/api/reviews/{review['id']}/report", headers=headers).json() == report

    insight = report["takeaways"][0]
    patched = client.patch(
        f"/api/reviews/{review['id']}/report/takeaways/insights/{insight['id']}",
        json={"status": "accepted", "correction": "This is accurate."},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["takeaways"][0]["status"] == "accepted"
    assert patched.json()["takeaways"][0]["correction"] == "This is accurate."


def test_commitment_endpoints_and_deletion_cascade(client_and_credentials):
    client, _, _, token = client_and_credentials
    headers = auth(token)
    week = date(2024, 3, 4)
    review = client.post("/api/reviews", json=review_payload(week), headers=headers).json()

    created = client.put(f"/api/reviews/{review['id']}/commitment", json={"text": "Practice", "measure": "Twice"}, headers=headers)
    assert created.status_code == 200
    commitment = created.json()
    assert client.get(f"/api/reviews/{review['id']}/commitment", headers=headers).json() == commitment
    before = client.get("/api/commitments/before", params={"weekStart": (week + timedelta(days=7)).isoformat()}, headers=headers)
    assert before.status_code == 200
    assert before.json()["id"] == commitment["id"]

    client.post(f"/api/reviews/{review['id']}/complete", headers=headers)
    deleted = client.delete(f"/api/reviews/{review['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/reviews/{review['id']}", headers=headers).json() is None
    assert client.get(f"/api/reviews/{review['id']}/report", headers=headers).json() is None
    assert client.get(f"/api/reviews/{review['id']}/commitment", headers=headers).json() is None


def test_delete_all_data_only_clears_authenticated_user(client_and_credentials):
    client, _, _, token = client_and_credentials
    headers = auth(token)
    other = client.post("/api/auth/register", json={"username": "still-here", "password": "another-password"}).json()["accessToken"]
    other_review = client.post("/api/reviews", json=review_payload(date(2024, 4, 1)), headers=auth(other)).json()
    assert client.get("/api/reviews", headers=headers).json()
    assert client.delete("/api/data", headers=headers).status_code == 204
    assert client.get("/api/reviews", headers=headers).json() == []
    assert [item["id"] for item in client.get("/api/reviews", headers=auth(other)).json()] == [other_review["id"]]
