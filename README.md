# PythonProject

This repository contains a FastAPI task queue API with persistent storage, JWT authentication, and file logging.

## Features

- SQLite/PostgreSQL persistence via `DATABASE_URL`
- Task statuses: `pending`, `processing`, `done`, `error`
- JWT authentication with username/password
- Rate limiting
- Background worker with error handling
- Configurable settings via `.env`
- Requeues pending and processing tasks from the database on startup

## Run locally

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust values:

```bash
copy .env.example .env
```

4. Start the API:

```bash
python main.py
```

Or directly with uvicorn:

```bash
uvicorn task_api:app --reload
```

## Run tests

```bash
pytest -q
```

## Docker

Build and run the container directly:

```bash
docker build -t task-api .
docker run --rm -p 8000:8000 --env-file .env task-api
```

Or use Docker Compose for local development and live reload of the project volume:

```bash
docker compose up --build
```

The `docker-compose.yml` file mounts the project folder into `/app`, passes `.env` into the container, and exposes port `8000`.

## Environment variables

Use `.env` or environment variables to configure the service.

```env
SECRET_KEY=
DATABASE_URL=sqlite:///./tasks.db
# For PostgreSQL, use a URL like:
# DATABASE_URL=postgresql://user:password@localhost:5432/task_db
RATE_LIMIT=5
RATE_LIMIT_WINDOW_SECONDS=60
ACCESS_TOKEN_EXPIRE_SECONDS=3600
REFRESH_TOKEN_EXPIRE_SECONDS=1209600
LOG_FILE=app.log
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ChangeMeStrongPassword1!
```

Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` to seed an administrator account on startup. For production, set `SECRET_KEY` to a strong random value and, if you need a shared task queue, configure `QUEUE_BACKEND=redis` with `REDIS_URL`.

## New API routes

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `POST /api/auth/revoke-all`
- `GET /api/auth/me`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `POST /api/projects/{project_id}/tasks`
- `GET /api/projects/{project_id}/tasks/{task_id}`
- `GET /healthz`

## API Endpoints

### Authentication

- `POST /register` - register a new user (returns JWT token)
- `POST /login` - login with username and password (returns JWT token)

### Tasks

- `POST /tasks` - create a task (requires Bearer token)
- `GET /tasks/{task_id}` - check task status and result (requires Bearer token)

## Example requests

### 1. Register a new user:

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "alice123"}'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Login:

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "alice123"}'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 3. Create a task:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"data": "hello world"}'
```

Response:

```json
{
  "task_id": "12345678-1234-1234-1234-123456789012"
}
```

### 4. Get task status:

```bash
curl -X GET http://localhost:8000/tasks/12345678-1234-1234-1234-123456789012 \
  -H "Authorization: Bearer <access_token>"
```

Response:

```json
{
  "id": "12345678-1234-1234-1234-123456789012",
  "status": "done",
  "result": "HELLO WORLD"
}
```

## Notes

- If `DATABASE_URL` is not provided, the app uses SQLite at `./tasks.db` by default.
- Log output is written to the file configured by `LOG_FILE`.
- The service uses a runtime `asyncio.Queue` to dispatch tasks to the worker, while task state and results are persisted in the database.
- The app requeues any pending or processing tasks on startup.
- Each user can only access and create their own tasks.
