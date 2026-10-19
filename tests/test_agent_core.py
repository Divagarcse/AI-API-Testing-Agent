from agent_core import parse_openapi, fallback_cases, _safe_case

def test_parse_openapi():
    spec = {"openapi":"3.0.0","paths":{"/users":{"get":{"responses":{"200":{"description":"ok"}}}}}}
    result = parse_openapi(spec)
    assert len(result) == 1
    assert result[0]["path"] == "/users"
    assert result[0]["method"] == "GET"


def test_fallback_cases_cover_crud_when_spec_has_it():
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "Users listed"}
                    }
                },
                "post": {
                    "responses": {
                        "201": {"description": "User created"}
                    }
                }
            },
            "/users/{user_id}": {
                "get": {
                    "responses": {
                        "200": {"description": "User found"},
                        "404": {"description": "User not found"}
                    }
                },
                "put": {
                    "responses": {
                        "200": {"description": "User updated"},
                        "404": {"description": "User not found"}
                    }
                },
                "delete": {
                    "responses": {
                        "204": {"description": "User deleted"},
                        "404": {"description": "User not found"}
                    }
                }
            }
        }
    }

    endpoints = parse_openapi(spec)
    cases = fallback_cases(endpoints)

    assert {c["method"] for c in cases} == {
        "GET", "POST", "PUT", "DELETE"
    }
    assert all(_safe_case(c, endpoints) for c in cases)


def test_unsafe_method_rejected():
    endpoints = parse_openapi({"paths":{"/users":{"get":{}}}})
    assert not _safe_case({"endpoint":"/users","method":"PATCH","path_params":{}}, endpoints)
