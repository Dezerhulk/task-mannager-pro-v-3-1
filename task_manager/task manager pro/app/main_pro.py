"""FastAPI application with REST API endpoints."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .crud_pro import seed_admin_user
from .database_pro import init_db
from .security import SecurityHeadersMiddleware
from .routers import ai, auth, users, projects, tasks, comments, tags, audit, notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database and seed admin user on startup."""
    init_db()
    seed_admin_user()
    yield


# FastAPI app
app = FastAPI(
    title="Task Manager Pro API",
    description="Advanced task management with SQLAlchemy + SQLite/PostgreSQL + FastAPI",
    version="2.0.0",
    lifespan=lifespan,
)

# Security headers (HSTS in production, CSP basics, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - configured from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# ===================== Include Routers =====================

app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(tags.router)
app.include_router(audit.router)
app.include_router(notifications.router)
app.include_router(ai.router)


# ===================== Health & Root =====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Task Manager Pro API",
        "version": "2.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

