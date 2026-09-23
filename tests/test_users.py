"""
Tests de la API de usuarios.
Cubre: crear, duplicado, listar paginado, get, get inexistente,
patch, patch email duplicado, soft delete, reactivar.
"""


def _create_user(client, name="Alice", email="alice@example.com", **kwargs):
    payload = {"name": name, "email": email, **kwargs}
    return client.post("/users", json=payload)


# ----------------------------
# POST /users
# ----------------------------
def test_create_user_returns_201(client):
    r = _create_user(client)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["tenant_id"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "api_key_hash" not in data  # nunca se expone


def test_create_user_with_role_and_tenant(client):
    r = _create_user(
        client,
        name="Bob",
        email="bob@example.com",
        role="admin",
        tenant_id="acme",
    )
    assert r.status_code == 201
    data = r.json()
    assert data["role"] == "admin"
    assert data["tenant_id"] == "acme"


def test_create_duplicate_email_returns_409(client):
    _create_user(client)
    r = _create_user(client, name="Other", email="alice@example.com")
    assert r.status_code == 409
    assert r.json()["detail"] == "Email already registered"


def test_create_invalid_email_returns_422(client):
    r = client.post("/users", json={"name": "X", "email": "not-an-email"})
    assert r.status_code == 422


def test_create_empty_name_returns_422(client):
    r = client.post("/users", json={"name": "", "email": "x@example.com"})
    assert r.status_code == 422


# ----------------------------
# GET /users
# ----------------------------
def test_list_users_empty(client):
    r = client.get("/users")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 50


def test_list_users_pagination(client):
    for i in range(5):
        _create_user(client, name=f"U{i}", email=f"u{i}@example.com")

    r = client.get("/users?skip=0&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    r2 = client.get("/users?skip=2&limit=2")
    data2 = r2.json()
    assert len(data2["items"]) == 2
    # IDs distintos entre páginas
    ids_page1 = {u["id"] for u in data["items"]}
    ids_page2 = {u["id"] for u in data2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


def test_list_users_invalid_limit_returns_422(client):
    r = client.get("/users?limit=0")
    assert r.status_code == 422
    r = client.get("/users?limit=999")
    assert r.status_code == 422


# ----------------------------
# GET /users/{id}
# ----------------------------
def test_get_user_by_id(client):
    created = _create_user(client).json()
    r = client.get(f"/users/{created['id']}")
    assert r.status_code == 200
    assert r.json()["email"] == created["email"]


def test_get_user_not_found_returns_404(client):
    r = client.get("/users/9999")
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


# ----------------------------
# PATCH /users/{id}
# ----------------------------
def test_patch_user_partial_update(client):
    created = _create_user(client).json()
    r = client.patch(f"/users/{created['id']}", json={"name": "Alicia"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Alicia"
    assert data["email"] == created["email"]  # no cambió
    assert data["role"] == "user"  # no cambió


def test_patch_user_email_conflict_returns_409(client):
    a = _create_user(client, name="A", email="a@example.com").json()
    _create_user(client, name="B", email="b@example.com")

    r = client.patch(f"/users/{a['id']}", json={"email": "b@example.com"})
    assert r.status_code == 409


def test_patch_user_not_found_returns_404(client):
    r = client.patch("/users/9999", json={"name": "X"})
    assert r.status_code == 404


# ----------------------------
# DELETE /users/{id} (soft)
# ----------------------------
def test_soft_delete_user(client):
    created = _create_user(client).json()
    r = client.delete(f"/users/{created['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["is_active"] is False

    # No aparece en listado por defecto
    listing = client.get("/users").json()
    assert listing["total"] == 0

    # Sí aparece si include_inactive=true
    listing_all = client.get("/users?include_inactive=true").json()
    assert listing_all["total"] == 1


def test_delete_not_found_returns_404(client):
    r = client.delete("/users/9999")
    assert r.status_code == 404


# ----------------------------
# POST /users/{id}/reactivate
# ----------------------------
def test_reactivate_user(client):
    created = _create_user(client).json()
    client.delete(f"/users/{created['id']}")

    r = client.post(f"/users/{created['id']}/reactivate")
    assert r.status_code == 200
    assert r.json()["is_active"] is True

    # Vuelve a aparecer en listado por defecto
    listing = client.get("/users").json()
    assert listing["total"] == 1


def test_reactivate_not_found_returns_404(client):
    r = client.post("/users/9999/reactivate")
    assert r.status_code == 404


# ----------------------------
# Health
# ----------------------------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "AI API Gateway"
    assert data["status"] == "running"
