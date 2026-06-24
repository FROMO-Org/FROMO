"""
Top-level OpenAPI contract tests.
Checks that all core routes are registered and globally consistent.
Per-route details live in each domain's test_contract.py.
"""


def test_all_core_routes_are_registered(app):
    paths = app.openapi()["paths"]

    assert "/" in paths
    assert "/health" in paths
    assert "/events/" in paths
    assert "/events/{event_id}" in paths
    assert "/venues/" in paths
    assert "/venues/{venue_id}" in paths
    assert "/organisations/" in paths
    assert "/organisations/me" in paths
    assert "/organisations/{organisation_id}/dashboard" in paths
    assert "/bookings/me" in paths
    assert "/saved-events/me" in paths
    assert "/busyness/nearby" in paths


def test_all_uuid_path_params_are_typed_as_uuid(app):
    paths = app.openapi()["paths"]

    checks = [
        ("/events/{event_id}", "get"),
        ("/venues/{venue_id}", "get"),
        ("/organisations/{organisation_id}", "get"),
    ]

    for path, method in checks:
        op = paths[path][method]
        uuid_param = next(p for p in op["parameters"] if "id" in p["name"])
        assert uuid_param["schema"]["format"] == "uuid", (
            f"{path} {method}: {uuid_param['name']} is not typed as uuid"
        )
