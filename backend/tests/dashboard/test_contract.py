"""
Contract and auth tests for the dashboard endpoint.
"""
from uuid import uuid4


def test_dashboard_requires_auth(client, fail_if_db_is_used):
    response = client.get(f"/organisations/{uuid4()}/dashboard")
    assert response.status_code == 401


def test_dashboard_organisation_id_param_is_uuid(app):
    operation = app.openapi()["paths"]["/organisations/{organisation_id}/dashboard"]["get"]
    schema = operation["parameters"][0]["schema"]
    assert schema["format"] == "uuid"


def test_dashboard_requires_auth_in_openapi(app):
    operation = app.openapi()["paths"]["/organisations/{organisation_id}/dashboard"]["get"]
    assert "security" in operation
