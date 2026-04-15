# Task Management API

A small **FastAPI** backend with **SQLite**, **SQLAlchemy 2.x**, and **Alembic** migrations. Tasks support create, list (with filters), status update, and delete.

## Features

- **POST /tasks** — Create a task; `status` defaults to `pending`.
- **GET /tasks** — List tasks, optional `status` and `start_date` / `end_date` filters; newest first.
- **PUT /tasks/{id}** — Update **only** `status` (`pending`, `in_progress`, `completed`).
- **DELETE /tasks/{id}** — Remove a task.
- **5-second duplicate title rule** — Second create with the same `title` within 5 seconds returns **409 Conflict**.
- **Pydantic** validation for request/response bodies.
- **Structured JSON errors** for conflicts, not found, and bad date ranges.
- **Request logging middleware** (method, path, status, duration, short request id).

## Project layout

```
app/
  core/
    config.py          # Settings (e.g. DATABASE_URL)
  database/
    base.py            # SQLAlchemy DeclarativeBase
    session.py         # Engine, SessionLocal, get_db
  models/
    task.py            # Task ORM model + TaskStatus enum
  routers/
    tasks.py           # Task routes
  schemas/
    task.py            # Pydantic schemas
  main.py              # FastAPI app, middleware, exception handler
alembic/
  versions/
    001_initial_tasks.py
  env.py
alembic.ini
requirements.txt
```

## Requirements

- Python **3.9+** (3.10+ recommended).
- Dependencies are listed in `requirements.txt`. On Windows, `greenlet` is pinned so pip can install a **binary wheel** without a C++ compiler.

## Setup

1. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database** (optional):

   Default is SQLite at `./tasks.db`. Override with an environment variable:

   ```bash
   set DATABASE_URL=sqlite:///./tasks.db
   ```

   For PostgreSQL later, use something like:

   ```bash
   set DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/tasks
   ```

4. **Run migrations**:

   ```bash
   python -m alembic upgrade head
   ```

## Run the API

From the project root:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: `GET /health`

## API usage examples

### Create task (201)

```bash
curl -s -X POST http://127.0.0.1:8000/tasks ^
  -H "Content-Type: application/json" ^
  -d "{\"title\": \"Buy milk\", \"description\": \"2% organic\"}"
```

**Example success response** (201):

```json
{
  "id": 1,
  "title": "Buy milk",
  "description": "2% organic",
  "status": "pending",
  "created_at": "2026-04-15T05:00:00Z"
}
```

### Duplicate title within 5 seconds (409)

```bash
curl -s -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Same\"}"
curl -s -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Same\"}"
```

**Example error response** (409):

```json
{
  "error": {
    "code": "duplicate_title",
    "message": "A task with this title was created within the last 5 seconds."
  }
}
```

### List tasks with filters (200)

```bash
curl -s "http://127.0.0.1:8000/tasks?status=pending"
curl -s "http://127.0.0.1:8000/tasks?start_date=2026-04-01T00:00:00Z&end_date=2026-04-30T23:59:59Z"
```

**Example response** (200):

```json
{
  "items": [
    {
      "id": 2,
      "title": "Write README",
      "description": null,
      "status": "pending",
      "created_at": "2026-04-15T05:01:00Z"
    }
  ],
  "count": 1
}
```

### Update status only (200)

```bash
curl -s -X PUT http://127.0.0.1:8000/tasks/1 ^
  -H "Content-Type: application/json" ^
  -d "{\"status\": \"in_progress\"}"
```

Invalid enum (e.g. `"status": "done"`) returns **422** with FastAPI validation details.

### Delete task (204 / 404)

```bash
curl -s -o NUL -w "%%{http_code}" -X DELETE http://127.0.0.1:8000/tasks/1
```

**Not found** (404):

```json
{
  "error": {
    "code": "not_found",
    "message": "Task with id 99 was not found."
  }
}
```

## Duplicate title rule (5 seconds)

On **POST /tasks**, the server looks for an existing row with the **same `title`** (case-sensitive) **and** `created_at` within the **last 5 seconds** (UTC). If found, the API returns **409 Conflict** with `code: duplicate_title`. After 5 seconds, the same title is allowed again.

## Example responses summary

| Situation | HTTP status | `error.code` (if any) |
|-----------|-------------|------------------------|
| Created | 201 | — |
| Duplicate title within 5s | 409 | `duplicate_title` |
| Task not found | 404 | `not_found` |
| Invalid date range (`start_date` > `end_date`) | 400 | `invalid_date_range` |
| Validation (e.g. bad status) | 422 | FastAPI default |

## Optional improvements

- **Authentication** — Add JWT or API keys; scope duplicate-title checks per user if `user_id` is present.
- **PostgreSQL in production** — Switch `DATABASE_URL` and run migrations against Postgres.
- **Pagination** — `limit` / `offset` or cursor on `GET /tasks`.
- **Rate limiting** — Protect create endpoint from abuse.
- **Tests** — `pytest` + `httpx` `TestClient` (already in `requirements.txt`).
- **Structured logging** — JSON logs for aggregation (ELK, CloudWatch).

## License

Use freely for learning or as a starting point for your own project.
