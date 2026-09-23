# AI API Gateway

[![CI](https://github.com/hectorquinterosilva/ai-api-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/hectorquinterosilva/ai-api-gateway/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688)
![License](https://img.shields.io/badge/license-MIT-green)

API Gateway construido con **FastAPI + PostgreSQL + Redis**, diseñado como base para plataformas de IA en producción: autenticación por API key, observabilidad, migraciones versionadas y stack Docker completo.

**Proyecto #21** del portafolio de [Héctor Andrés Quintero Silva](https://github.com/hectorquinterosilva).

---

## Stack

| Capa | Tecnología |
|---|---|
| Framework | FastAPI 0.138 + Starlette 1.3 |
| ORM | SQLAlchemy 2.0 (tipado, `Mapped`) |
| Migraciones | Alembic 1.18 |
| Base de datos | PostgreSQL 18 |
| Cache / colas | Redis 7 |
| Config | pydantic-settings (12-factor) |
| Auth | API key por header `X-API-Key`, SHA-256 |
| Observabilidad | Logs JSON, `/metrics` Prometheus, `X-Request-ID` |
| Tests | pytest + httpx + SQLite in-memory |
| Contenedores | Docker + Docker Compose |

---

## Arquitectura

```
app/
├── api/            # Endpoints HTTP (routers FastAPI)
│   ├── deps.py     # Dependencias (auth, DB)
│   └── users.py    # CRUD + rotación de API keys
├── core/           # Config, logging, métricas, seguridad, redis
├── db/             # Base declarativa, engine, sesión
├── exceptions/     # Excepciones de dominio
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
├── services/       # Lógica de negocio
└── main.py         # App FastAPI, health checks, /metrics
```

**Capas:** `api` (HTTP) → `services` (lógica) → `models` (persistencia).
Las excepciones de dominio viven en `exceptions/` y se traducen a HTTP en `api/`.

---

## Requisitos

- Docker y Docker Compose
- (Opcional, desarrollo local) Python 3.12+, PostgreSQL, Redis

---

## Arranque rápido

```bash
# 1. Clonar
git clone https://github.com/hectorquinterosilva/ai-api-gateway.git
cd ai-api-gateway

# 2. Variables de entorno
cp .env.example .env
# Edita .env si necesitas cambiar credenciales

# 3. Levantar todo
docker compose up -d --build

# 4. Aplicar migraciones
docker compose exec api alembic upgrade head

# 5. Verificar
curl http://localhost:8000/health/ready
```

Documentación interactiva: <http://localhost:8000/docs>

---

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/users` | público | Registrar usuario (devuelve API key) |
| `GET` | `/users/me` | API key | Perfil propio |
| `GET` | `/users` | API key | Listar (paginado) |
| `GET` | `/users/{id}` | API key | Obtener uno |
| `PATCH` | `/users/{id}` | API key | Actualizar parcial |
| `DELETE` | `/users/{id}` | API key | Soft delete |
| `POST` | `/users/{id}/reactivate` | API key | Reactivar |
| `POST` | `/users/{id}/api-key` | API key | Rotar API key |
| `DELETE` | `/users/{id}/api-key` | API key | Revocar API key |
| `GET` | `/health` `/health/live` | público | Liveness |
| `GET` | `/health/ready` | público | Readiness (DB + Redis) |
| `GET` | `/metrics` | público | Métricas Prometheus |

---

## Autenticación

Cada usuario al registrarse recibe una API key en claro **una sola vez**. Se guarda únicamente su hash SHA-256.

```bash
# Registro
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
# → {"id": 1, ..., "api_key": "aigw_..."}

# Uso
curl http://localhost:8000/users/me -H "X-API-Key: aigw_..."
```

Si pierdes la key, se rota con `POST /users/{id}/api-key` (la vieja deja de funcionar inmediatamente).

---

## Observabilidad

**Logs JSON estructurados** con contexto por request:

```json
{"timestamp":"...","level":"INFO","logger":"app.request","message":"request completed","request_id":"...","method":"GET","path":"/health","status_code":200,"duration_ms":11.75,"client_ip":"172.18.0.1"}
```

**Métricas Prometheus** en `/metrics`:

```
http_requests_total{method="GET",path="/health",status_code="200"} 42.0
http_request_duration_seconds_bucket{method="GET",path="/health",le="0.01"} 40.0
```

**Request ID** propagado en `X-Request-ID` (acepta uno entrante o genera UUID).

---

## Tests

```bash
docker compose exec api pytest
# o local:
pytest
```

35 tests cubriendo auth, CRUD, paginación, soft delete, rotación de keys, health checks, logging y métricas. SQLite in-memory, sin dependencias externas.

---

## Desarrollo local (sin Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
# Ajusta POSTGRES_HOST=localhost, REDIS_HOST=localhost

alembic upgrade head
uvicorn app.main:app --reload
```

---

## Roadmap

- [x] Auth por API key con rotación
- [x] Migraciones Alembic
- [x] Health checks (liveness + readiness)
- [x] Logs JSON + request ID
- [x] Métricas Prometheus
- [x] CI con GitHub Actions
- [ ] Rate limiting por API key (proyecto #31)
- [ ] RBAC con roles y permisos (proyecto #24)
- [ ] Multi-tenant completo (proyecto #26)
- [ ] Integración con proveedores LLM (proyecto #120)

---

## Licencia

MIT — ver [LICENSE](LICENSE).