"""
Tests de la API de usuarios con autenticación por API key.
"""


def _register(client, name="Alice", email="alice@example.com", **kwargs):
    payload = {"name": name, "email": email, **kwargs}
    return client.post("/users", json=payload)


def _auth(key: str) -> dict:
    return {"X-API-Key": key}


# ============================================================
# Registro (público)
# ============================================================
def test_register_returns_201_with_api_key(client):
    r = _register(client)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["api_key"].startswith("aigw_")
    assert "api_key_hash" not in data


def test_register_duplicate_email_returns_409(client):
    _register(client)
    r = _register(client, name="Other")
    assert r.status_code == 409


def test_register_invalid_email_returns_422(client):
    r = client.post("/users", json={"name": "X", "email": "not-an-email"})
    assert r.status_code == 422


def test_register_empty_name_returns_422(client):
    r = client.post("/users", json={"name": "", "email": "x@example.com"})
    assert r.status_code == 422


# ============================================================
# Auth
# ============================================================
def test_protected_route_without_key_returns_401(client):
    r = client.get("/users")
    assert r.status_code == 401
    assert "Missing" in r.json()["detail"]


def test_protected_route_with_invalid_key_returns_401(client):
    r = client.get("/users", headers=_auth("aigw_invalid_key_here"))
    assert r.status_code == 401
    assert "Invalid" in r.json()["detail"]


def test_get_me(client):
    reg = _register(client).json()
    r = client.get("/users/me", headers=_auth(reg["api_key"]))
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_protected_route_with_valid_key_returns_200(client):
    reg = _register(client).json()
    r = client.get("/users", headers=_auth(reg["api_key"]))
    assert r.status_code == 200


# ============================================================
# Listar
# ============================================================
def test_list_users_returns_self(client):
    """Al registrarse, el usuario debe verse a sí mismo en el listado."""
    reg = _register(client).json()
    r = client.get("/users", headers=_auth(reg["api_key"]))
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == reg["id"]


def test_list_users_pagination(client):
    reg = _register(client, name="Admin", email="admin@example.com").json()
    key = reg["api_key"]

    for i in range(5):
        _register(client, name=f"U{i}", email=f"u{i}@example.com")

    r = client.get("/users?skip=0&limit=2", headers=_auth(key))
    data = r.json()
    assert data["total"] == 6
    assert len(data["items"]) == 2

    r2 = client.get("/users?skip=2&limit=2", headers=_auth(key))
    data2 = r2.json()
    ids_1 = {u["id"] for u in data["items"]}
    ids_2 = {u["id"] for u in data2["items"]}
    assert ids_1.isdisjoint(ids_2)


def test_list_users_invalid_limit_returns_422(client):
    reg = _register(client).json()
    r = client.get("/users?limit=0", headers=_auth(reg["api_key"]))
    assert r.status_code == 422
    r = client.get("/users?limit=999", headers=_auth(reg["api_key"]))
    assert r.status_code == 422


# ============================================================
# Get por id
# ============================================================
def test_get_user_by_id(client):
    reg = _register(client).json()
    key = reg["api_key"]
    r = client.get(f"/users/{reg['id']}", headers=_auth(key))
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_get_user_not_found_returns_404(client):
    reg = _register(client).json()
    r = client.get("/users/9999", headers=_auth(reg["api_key"]))
    assert r.status_code == 404


# ============================================================
# PATCH
# ============================================================
def test_patch_user_partial_update(client):
    reg = _register(client).json()
    key = reg["api_key"]
    r = client.patch(
        f"/users/{reg['id']}",
        json={"name": "Alicia"},
        headers=_auth(key),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Alicia"
    assert data["email"] == "alice@example.com"


def test_patch_email_conflict_returns_409(client):
    a = _register(client, name="A", email="a@example.com").json()
    b = _register(client, name="B", email="b@example.com").json()

    r = client.patch(
        f"/users/{a['id']}",
        json={"email": "b@example.com"},
        headers=_auth(a["api_key"]),
    )
    assert r.status_code == 409


def test_patch_not_found_returns_404(client):
    reg = _register(client).json()
    r = client.patch(
        "/users/9999",
        json={"name": "X"},
        headers=_auth(reg["api_key"]),
    )
    assert r.status_code == 404


# ============================================================
# Soft delete / reactivar
# ============================================================
def test_soft_delete_user(client):
    reg = _register(client).json()
    key = reg["api_key"]

    r = client.delete(f"/users/{reg['id']}", headers=_auth(key))
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r2 = client.get("/users", headers=_auth(key))
    assert r2.status_code == 401


def test_delete_not_found_returns_404(client):
    reg = _register(client).json()
    r = client.delete("/users/9999", headers=_auth(reg["api_key"]))
    assert r.status_code == 404


def test_reactivate_user(client):
    a = _register(client, name="A", email="a@example.com").json()
    b = _register(client, name="B", email="b@example.com").json()

    client.delete(f"/users/{a['id']}", headers=_auth(a["api_key"]))

    r = client.post(
        f"/users/{a['id']}/reactivate",
        headers=_auth(b["api_key"]),
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is True


def test_reactivate_not_found_returns_404(client):
    reg = _register(client).json()
    r = client.post(
        "/users/9999/reactivate",
        headers=_auth(reg["api_key"]),
    )
    assert r.status_code == 404


# ============================================================
# Rotación / revocación de API key
# ============================================================
def test_rotate_api_key(client):
    reg = _register(client).json()
    old_key = reg["api_key"]

    r = client.post(
        f"/users/{reg['id']}/api-key",
        headers=_auth(old_key),
    )
    assert r.status_code == 200
    new_key = r.json()["api_key"]
    assert new_key.startswith("aigw_")
    assert new_key != old_key

    r_old = client.get("/users", headers=_auth(old_key))
    assert r_old.status_code == 401

    r_new = client.get("/users", headers=_auth(new_key))
    assert r_new.status_code == 200


def test_rotate_other_user_key_returns_403(client):
    a = _register(client, name="A", email="a@example.com").json()
    b = _register(client, name="B", email="b@example.com").json()

    r = client.post(
        f"/users/{b['id']}/api-key",
        headers=_auth(a["api_key"]),
    )
    assert r.status_code == 403


def test_revoke_api_key(client):
    reg = _register(client).json()
    key = reg["api_key"]

    r = client.delete(
        f"/users/{reg['id']}/api-key",
        headers=_auth(key),
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is True

    r2 = client.get("/users", headers=_auth(key))
    assert r2.status_code == 401


# ============================================================
# Health
# ============================================================
def test_health_liveness(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_ready_all_ok(client, monkeypatch):
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "_check_database", lambda: True)
    monkeypatch.setattr(main_mod, "check_redis", lambda: True)

    r = client.get("/health/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "ok"


def test_health_ready_redis_down(client, monkeypatch):
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "_check_database", lambda: True)
    monkeypatch.setattr(main_mod, "check_redis", lambda: False)

    r = client.get("/health/ready")
    assert r.status_code == 503
    data = r.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "error"


def test_health_ready_database_down(client, monkeypatch):
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "_check_database", lambda: False)
    monkeypatch.setattr(main_mod, "check_redis", lambda: True)

    r = client.get("/health/ready")
    assert r.status_code == 503
    data = r.json()
    assert data["status"] == "degraded"
    assert data["checks"]["database"] == "error"
    assert data["checks"]["redis"] == "ok"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "AI API Gateway"
    assert data["status"] == "running"
