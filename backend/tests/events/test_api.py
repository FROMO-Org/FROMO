"""
HTTP behaviour tests for /events/.
Uses TestClient with mocked DB and auth — no real DB needed.
"""
from uuid import uuid4


class TestEventListValidation:
    def test_requires_both_lat_and_lng(self, client):
        response = client.get("/events/?lat=51.5")
        assert response.status_code == 400
        assert "lat and lng must be provided together" in response.json()["detail"]

    def test_rejects_lat_out_of_range(self, client):
        response = client.get("/events/?lat=200&lng=0")
        assert response.status_code == 422

    def test_rejects_lng_out_of_range(self, client):
        response = client.get("/events/?lat=0&lng=200")
        assert response.status_code == 422

    def test_rejects_invalid_limit(self, client):
        response = client.get("/events/?limit=0")
        assert response.status_code == 422

    def test_rejects_limit_over_max(self, client):
        response = client.get("/events/?limit=101")
        assert response.status_code == 422


class TestEventDetailValidation:
    def test_invalid_uuid_returns_422(self, client):
        response = client.get("/events/not-a-uuid")
        assert response.status_code == 422


class TestEventCreateAuth:
    def test_unauthenticated_request_returns_401(self, client):
        response = client.post("/events/", json={})
        assert response.status_code == 401

    def test_authenticated_request_with_missing_body_returns_422(self, authenticated_client):
        response = authenticated_client.post("/events/", json={})
        assert response.status_code == 422


class TestEventUpdateAuth:
    def test_unauthenticated_patch_returns_401(self, client):
        response = client.patch(f"/events/{uuid4()}", json={"title": "New title"})
        assert response.status_code == 401


class TestEventDeleteAuth:
    def test_unauthenticated_delete_returns_401(self, client):
        response = client.delete(f"/events/{uuid4()}")
        assert response.status_code == 401
