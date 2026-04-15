# Task Management API (FastAPI + MySQL)

Backend API for creating, listing, updating, editing, and deleting tasks.
Includes:
- JSON API endpoints
- Browser Task UI
- ReDoc API documentation

## Tech Stack

- Python + FastAPI
- MySQL
- SQLAlchemy ORM
- Pydantic validation
- Environment variables via `python-dotenv`

## Project Structure

```
app/
│── main.py
│── database/
│   ├── connection.py
│   ├── base.py
│── models/
│   ├── task.py
│── schemas/
│   ├── task.py
│── routers/
│   ├── task_router.py
│── services/
│   ├── task_service.py
│── middleware/
│   ├── logging.py
│── core/
│   ├── config.py
│
.env
requirements.txt
README.md
```

## MySQL Setup

1. Ensure MySQL is running on:
   - host: `localhost`
   - port: `3306`

2. Create the database:

```sql
CREATE DATABASE task_db;
```

3. The required `.env` is already included and must remain exactly:

```env
DATABASE_URL=mysql+pymysql://root:Password/localhost:3306/task_db
```

Note: `#` is a reserved URL character; the application safely encodes it internally at runtime so SQLAlchemy can connect.

## Installation

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload --port 8011
```

Or run using the module entrypoint:

```bash
python app/main.py
```

## App URLs

- Task UI (root): `http://127.0.0.1:8011/`
- Task UI (alias): `http://127.0.0.1:8011/ui`
- ReDoc: `http://127.0.0.1:8011/redoc`
- Health check: `http://127.0.0.1:8011/health`

## API Endpoints

### 1) Create Task

**POST** `/tasks`

Request:

```json
{
  "title": "My Task",
  "description": "Optional details"
}
```

Success (201):

```json
{
  "id": 1,
  "title": "My Task",
  "description": "Optional details",
  "status": "pending",
  "created_at": "2026-04-15T10:20:30"
}
```

Validation:
- `title` is required
- `title` length: 1 to 255

### 2) Get Tasks (optional filters)

**GET** `/tasks`

Query params:
- `status` (optional): `pending | in_progress | completed`
- `start_date` (optional): ISO datetime (e.g. `2026-04-15T00:00:00`)
- `end_date` (optional): ISO datetime

Example:

```bash
curl "http://127.0.0.1:8011/tasks?status=pending"
```

Response (200, newest first):

```json
[
  {
    "id": 2,
    "title": "Newest task",
    "description": null,
    "status": "pending",
    "created_at": "2026-04-15T10:21:00"
  }
]
```

### 3) Update Task Status Only

**PUT** `/tasks/{id}`

Request:

```json
{
  "status": "completed"
}
```

Success (200):

```json
{
  "id": 1,
  "title": "My Task",
  "description": "Optional details",
  "status": "completed",
  "created_at": "2026-04-15T10:20:30"
}
```

### 4) Edit Task Title/Description

**PUT** `/tasks/{id}/edit`

Request:

```json
{
  "title": "Updated title",
  "description": "Updated description"
}
```

Success (200):

```json
{
  "id": 1,
  "title": "Updated title",
  "description": "Updated description",
  "status": "pending",
  "created_at": "2026-04-15T10:20:30"
}
```

### 5) Delete Task

**DELETE** `/tasks/{id}`

Success (200):

```json
{
  "message": "Task deleted"
}
```

If not found (404):

```json
{
  "error": "Task not found"
}
```

## Error Responses

### Duplicate task in 5-second window

- Condition: same `title` created within last 5 seconds
- Response: **409 Conflict**

```json
{
  "error": "Task with same title created recently"
}
```

### Validation errors

- FastAPI returns **422 Unprocessable Entity** for invalid payload/query formats.

## Notes on Business Rule

A task cannot be created if another task with the same title exists in the past 5 seconds.

MySQL-style logic:

```sql
SELECT * FROM tasks
WHERE title = ?
AND created_at >= NOW() - INTERVAL 5 SECOND;
```

## Middleware Logging

Each request logs:
- HTTP method
- URL path
- execution time (ms)

Example output:
```
POST /tasks 12.34ms
```

## Current Route Summary

- `GET /` -> Task UI (HTML)
- `GET /ui` -> Task UI (HTML alias)
- `GET /health` -> JSON health response
- `GET /redoc` -> ReDoc documentation
- `POST /tasks` -> Create task
- `GET /tasks` -> List/filter tasks
- `PUT /tasks/{id}` -> Update status only
- `PUT /tasks/{id}/edit` -> Edit title/description
- `DELETE /tasks/{id}` -> Delete task

## Bonus: Suggested Improvements (Optional)

- Add Alembic migrations instead of `create_all` at startup
- Add pagination to `GET /tasks`
- Add user ownership/authentication
- Add unique constraints / idempotency keys for stronger duplicate protection across distributed systems


