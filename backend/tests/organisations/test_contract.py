"""
Contract and auth tests for /organisations/.
"""
from uuid import uuid4


def _paths(app):
    return app.openapi()["paths"]


class TestOrganisationRoutes:
    def test_core_routes_exist(self, app):
        paths = _paths(app)
        assert "/organisations/" in paths
        assert "/organisations/me" in paths
        assert "/organisations/{organisation_id}" in paths
        assert "/organisations/{organisation_id}/events" in paths
        assert "/organisations/{organisation_id}/members" in paths

    def test_create_organisation_requires_auth(self, app):
        op = _paths(app)["/organisations/"]["post"]
        assert "security" in op

    def test_add_member_requires_auth(self, app):
        op = _paths(app)["/organisations/{organisation_id}/members"]["post"]
        assert "security" in op

    def test_organisation_id_is_uuid(self, app):
        op = _paths(app)["/organisations/{organisation_id}"]["get"]
        assert op["parameters"][0]["schema"]["format"] == "uuid"


class TestOrganisationAuth:
    def test_create_organisation_unauthenticated_returns_401(self, client):
        response = client.post("/organisations/", json={"name": "Test Org"})
        assert response.status_code == 401

    def test_get_my_organisations_unauthenticated_returns_401(self, client):
        response = client.get("/organisations/me")
        assert response.status_code == 401

    def test_add_member_unauthenticated_returns_401(self, client):
        response = client.post(
            f"/organisations/{uuid4()}/members",
            json={"user_id": str(uuid4()), "role": "staff"},
        )
        assert response.status_code == 401
