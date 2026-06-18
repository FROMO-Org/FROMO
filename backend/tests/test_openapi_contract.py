def openapi_paths(app) -> dict:
    return app.openapi()["paths"]


def test_openapi_exposes_core_routes(app):
    paths = openapi_paths(app)

    assert "/" in paths
    assert "/health" in paths
    assert "/events/" in paths
    assert "/events/{event_id}" in paths
    assert "/venues/" in paths
    assert "/venues/{venue_id}" in paths
    assert "/organisations/" in paths
    assert "/organisations/me" in paths
    assert "/bookings/me" in paths
    assert "/saved-events/me" in paths
    assert "/busyness/nearby" in paths


def test_events_list_documents_expected_query_params(app):
    operation = openapi_paths(app)["/events/"]["get"]
    param_names = {param["name"] for param in operation["parameters"]}

    assert {"status", "lat", "lng", "radius_km", "limit", "offset"} <= param_names


def test_uuid_path_params_are_documented_as_uuid(app):
    paths = openapi_paths(app)

    event_id_schema = paths["/events/{event_id}"]["get"]["parameters"][0]["schema"]
    venue_id_schema = paths["/venues/{venue_id}"]["get"]["parameters"][0]["schema"]

    assert event_id_schema["format"] == "uuid"
    assert venue_id_schema["format"] == "uuid"


def test_venue_creation_request_body_uses_create_venue_schema(app):
    operation = openapi_paths(app)["/venues/"]["post"]
    body_schema = operation["requestBody"]["content"]["application/json"]["schema"]

    assert body_schema["$ref"] == "#/components/schemas/CreateVenueBody"


def test_venue_creation_requires_auth_in_openapi(app):
    operation = openapi_paths(app)["/venues/"]["post"]

    assert "security" in operation
