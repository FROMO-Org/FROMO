def get_event_paths(app) -> dict:
    schema = app.openapi()
    return schema["paths"]["/events/"]["get"]


def test_events_list_has_frontend_filters(app):
    events_get = get_event_paths(app)

    param_names = {param["name"] for param in events_get["parameters"]}

    assert "status" in param_names
    assert "category" in param_names
    assert "discounted_only" in param_names
    assert "starts_after" in param_names
    assert "starts_before" in param_names
    assert "has_spots" in param_names
    assert "lat" in param_names
    assert "lng" in param_names
    assert "radius_km" in param_names
    assert "limit" in param_names
    assert "offset" in param_names


def test_events_status_param_uses_event_status_enum(app):
    events_get = get_event_paths(app)

    status_param = next(
        param for param in events_get["parameters"]
        if param["name"] == "status"
    )

    status = status_param["schema"]["anyOf"][0]["enum"]

    assert status == ["draft", "active", "cancelled", "completed"]


def test_invalid_event_uuid_returns_422(client):
    response = client.get("/events/not-a-uuid")

    assert response.status_code == 422


def test_events_requires_lat_and_lng_together(client):
    response = client.get("/events/?lat=40.758")

    assert response.status_code == 400
    assert response.json()["detail"] == "lat and lng must be provided together"
