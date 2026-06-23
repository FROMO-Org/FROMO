"""
OpenAPI contract tests for /events/.
Check that routes exist, params are typed correctly, and auth is declared.
No HTTP calls, no DB.
"""


def _events_list_op(app):
    return app.openapi()["paths"]["/events/"]["get"]


def _events_detail_op(app):
    return app.openapi()["paths"]["/events/{event_id}"]["get"]


def _events_create_op(app):
    return app.openapi()["paths"]["/events/"]["post"]


class TestEventListContract:
    def test_route_exists(self, app):
        assert "/events/" in app.openapi()["paths"]

    def test_has_all_filter_params(self, app):
        param_names = {p["name"] for p in _events_list_op(app)["parameters"]}
        expected = {
            "status", "category", "discounted_only",
            "starts_after", "starts_before", "has_spots",
            "lat", "lng", "radius_km", "limit", "offset",
        }
        assert expected <= param_names

    def test_status_param_is_event_status_enum(self, app):
        params = _events_list_op(app)["parameters"]
        status_param = next(p for p in params if p["name"] == "status")
        enum_values = status_param["schema"]["anyOf"][0]["enum"]
        assert set(enum_values) == {"draft", "active", "cancelled", "completed"}

    def test_lat_lng_have_coordinate_bounds(self, app):
        params = {p["name"]: p for p in _events_list_op(app)["parameters"]}
        assert params["lat"]["schema"]["anyOf"][0]["maximum"] == 90
        assert params["lng"]["schema"]["anyOf"][0]["maximum"] == 180


class TestEventDetailContract:
    def test_route_exists(self, app):
        assert "/events/{event_id}" in app.openapi()["paths"]

    def test_event_id_is_uuid(self, app):
        param = _events_detail_op(app)["parameters"][0]
        assert param["schema"]["format"] == "uuid"


class TestEventCreateContract:
    def test_requires_auth(self, app):
        assert "security" in _events_create_op(app)

    def test_uses_create_event_body_schema(self, app):
        body_ref = _events_create_op(app)["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        assert "CreateEventBody" in body_ref
