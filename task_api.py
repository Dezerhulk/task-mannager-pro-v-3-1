import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    validate_password,
    verify_refresh_token,
    verify_token,
)
from config import ADMIN_PASSWORD, ADMIN_USERNAME, LOG_FILE
from database import (
    Project,
    ProjectMember,
    Task,
    User,
    get_db,
    init_db,
    SessionLocal,
)
from models import (
    LoginRequest,
    ProjectCreate,
    ProjectSummary,
    ProjectTaskCreate,
    RefreshRequest,
    RegisterRequest,
    TaskCreate,
    TaskState,
    TaskStatus,
    TokenResponse,
    UserProfile,
)
from storage import queue, rate_limiter
from worker import worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("task_app")


def get_user(db, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_project_member(db, project_id: str, username: str) -> ProjectMember | None:
    return (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.username == username,
        )
        .first()
    )


def get_project_role(db, project: Project, username: str) -> str:
    if project.owner == username:
        return "owner"
    member = get_project_member(db, project.id, username)
    return member.role if member else "none"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")

    with SessionLocal() as db:
        existing_admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if ADMIN_PASSWORD:
            if existing_admin is None:
                validate_password(ADMIN_PASSWORD)
                db.add(
                    User(
                        username=ADMIN_USERNAME,
                        hashed_password=hash_password(ADMIN_PASSWORD),
                        role="admin",
                    )
                )
                db.commit()
                logger.info("Seeded administrator account: %s", ADMIN_USERNAME)
            elif existing_admin.role != "admin":
                existing_admin.role = "admin"
                db.commit()
                logger.info("Upgraded existing user to admin: %s", ADMIN_USERNAME)

        pending_tasks = db.query(Task).filter(
            Task.status.in_([TaskState.pending.value, TaskState.processing.value])
        ).all()

        for stored_task in pending_tasks:
            stored_task.status = TaskState.pending.value
            await queue.put(stored_task.id)

        if pending_tasks:
            db.commit()
            logger.info("Requeued %d tasks from the database", len(pending_tasks))

    asyncio.create_task(worker())
    yield


app = FastAPI(lifespan=lifespan)

# Allow the local frontend dev server to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenResponse, dependencies=[rate_limiter("register")])
async def register(register_request: RegisterRequest, db=Depends(get_db)):
    existing_user = db.query(User).filter(User.username == register_request.username).first()
    if existing_user:
        logger.warning("Registration attempt with existing username: %s", register_request.username)
        raise HTTPException(status_code=400, detail="Username already exists")

    try:
        validate_password(register_request.password)
    except ValueError as invalid:
        raise HTTPException(status_code=400, detail=str(invalid)) from invalid

    try:
        new_user = User(
            username=register_request.username,
            hashed_password=hash_password(register_request.password),
            role="viewer",
        )
        db.add(new_user)
        db.commit()
        logger.info("New user registered: %s", register_request.username)
        access_token = create_access_token(register_request.username)
        refresh_token = create_refresh_token(db, register_request.username)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except SQLAlchemyError as err:
        db.rollback()
        logger.exception("Database error during user registration: %s", register_request.username)
        raise HTTPException(status_code=500, detail="Failed to register user") from err


@app.post("/register", response_model=TokenResponse, dependencies=[rate_limiter("register")])
async def register_legacy(register_request: RegisterRequest, db=Depends(get_db)):
    return await register(register_request, db)


@app.post("/api/auth/login", response_model=TokenResponse, dependencies=[rate_limiter("login")])
async def login(login_request: LoginRequest, db=Depends(get_db)):
    user = authenticate_user(db, login_request.username, login_request.password)
    if not user:
        logger.warning("Unauthorized login attempt for user: %s", login_request.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token(db, user.username)
    logger.info("User logged in: %s", user.username)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/login", response_model=TokenResponse, dependencies=[rate_limiter("login")])
async def login_legacy(login_request: LoginRequest, db=Depends(get_db)):
    return await login(login_request, db)


@app.post("/api/auth/refresh", response_model=TokenResponse, dependencies=[rate_limiter("refresh")])
async def refresh_tokens(refresh_request: RefreshRequest, db=Depends(get_db)):
    username = verify_refresh_token(db, refresh_request.refresh_token)
    revoke_refresh_token(db, refresh_request.refresh_token)
    access_token = create_access_token(username)
    refresh_token = create_refresh_token(db, username)
    logger.info("Refresh token rotated for user: %s", username)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/api/auth/logout")
async def logout(refresh_request: RefreshRequest, db=Depends(get_db)):
    revoke_refresh_token(db, refresh_request.refresh_token)
    logger.info("Refresh token revoked via logout")
    return JSONResponse({"detail": "Logged out successfully"})


@app.post("/api/auth/revoke-all")
async def revoke_all_tokens(current_user: str = Depends(verify_token), db=Depends(get_db)):
    count = revoke_all_refresh_tokens(db, current_user)
    logger.info("Revoked %d refresh tokens for user %s", count, current_user)
    return {"revoked": count}


@app.get("/api/auth/me", response_model=UserProfile)
async def me(current_user: str = Depends(verify_token), db=Depends(get_db)):
    user = get_user(db, current_user)
    return UserProfile(username=user.username, role=user.role)


@app.post("/tasks", dependencies=[rate_limiter("tasks")])
async def create_task(task: TaskCreate, user: str = Depends(verify_token), db=Depends(get_db)):
    task_id = str(uuid.uuid4())
    db_task = Task(
        id=task_id,
        status=TaskState.pending.value,
        data=task.data,
        result=None,
        user=user,
    )
    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        await queue.put(task_id)
        logger.info("Task %s created by user %s", task_id, user)
        return {"task_id": task_id}
    except SQLAlchemyError as err:
        db.rollback()
        logger.exception("Database error while creating task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to create task") from err


@app.get("/tasks/{task_id}", response_model=TaskStatus, dependencies=[rate_limiter("tasks")])
async def get_task(task_id: str, user: str = Depends(verify_token), db=Depends(get_db)):
    try:
        task = db.get(Task, task_id)
    except SQLAlchemyError as err:
        logger.exception("Database error while reading task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve task") from err

    if not task:
        logger.warning("Task %s not found for user %s", task_id, user)
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user != user and task.assignee != user:
        logger.warning("Forbidden access to task %s by user %s", task_id, user)
        raise HTTPException(status_code=403, detail="Forbidden")

    return TaskStatus(
        id=task.id,
        status=task.status,
        result=task.result,
        title=task.title,
        description=task.description,
        assignee=task.assignee,
        project_id=task.project_id,
    )


@app.get("/api/projects", response_model=List[ProjectSummary])
async def list_projects(current_user: str = Depends(verify_token), db=Depends(get_db)):
    owned = db.query(Project).filter(Project.owner == current_user).all()
    member_projects = (
        db.query(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(ProjectMember.username == current_user)
        .all()
    )
    projects = {project.id: project for project in owned + member_projects}
    summaries = []
    for project in projects.values():
        role = get_project_role(db, project, current_user)
        summaries.append(
            ProjectSummary(
                id=project.id,
                title=project.title,
                description=project.description,
                owner=project.owner,
                role=role,
            )
        )
    return summaries


@app.post("/api/projects", response_model=ProjectSummary)
async def create_project(
    payload: ProjectCreate,
    current_user: str = Depends(verify_token),
    db=Depends(get_db),
):
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        title=payload.title,
        description=payload.description,
        owner=current_user,
    )
    membership = ProjectMember(
        project_id=project_id,
        username=current_user,
        role="owner",
    )
    try:
        db.add(project)
        db.add(membership)
        db.commit()
        logger.info("Project %s created by user %s", project_id, current_user)
        return ProjectSummary(
            id=project.id,
            title=project.title,
            description=project.description,
            owner=project.owner,
            role="owner",
        )
    except SQLAlchemyError as err:
        db.rollback()
        logger.exception("Database error creating project %s", project_id)
        raise HTTPException(status_code=500, detail="Failed to create project") from err


@app.get("/api/projects/{project_id}", response_model=ProjectSummary)
async def get_project(project_id: str, current_user: str = Depends(verify_token), db=Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = get_project_role(db, project, current_user)
    if role == "none":
        raise HTTPException(status_code=403, detail="Forbidden")
    return ProjectSummary(
        id=project.id,
        title=project.title,
        description=project.description,
        owner=project.owner,
        role=role,
    )


@app.post("/api/projects/{project_id}/tasks")
async def create_project_task(
    project_id: str,
    payload: ProjectTaskCreate,
    current_user: str = Depends(verify_token),
    db=Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = get_project_role(db, project, current_user)
    if role not in {"owner", "admin", "member"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    task_id = str(uuid.uuid4())
    db_task = Task(
        id=task_id,
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        assignee=payload.assignee,
        status=TaskState.pending.value,
        user=current_user,
    )
    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        await queue.put(task_id)
        logger.info("Project task %s created in project %s by %s", task_id, project_id, current_user)
        return {
            "task_id": task_id,
            "project_id": project_id,
            "title": db_task.title,
            "description": db_task.description,
            "assignee": db_task.assignee,
            "status": db_task.status,
        }
    except SQLAlchemyError as err:
        db.rollback()
        logger.exception("Database error creating project task %s", task_id)
        raise HTTPException(status_code=500, detail="Failed to create project task") from err


@app.get("/api/projects/{project_id}/tasks/{task_id}", response_model=TaskStatus)
async def get_project_task(project_id: str, task_id: str, current_user: str = Depends(verify_token), db=Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = get_project_role(db, project, current_user)
    if role == "none":
        raise HTTPException(status_code=403, detail="Forbidden")

    task = db.get(Task, task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatus(
        id=task.id,
        status=task.status,
        result=task.result,
        title=task.title,
        description=task.description,
        assignee=task.assignee,
        project_id=task.project_id,
    )


@app.get("/api/projects/{project_id}/tasks", response_model=List[TaskStatus])
async def list_project_tasks(project_id: str, current_user: str = Depends(verify_token), db=Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = get_project_role(db, project, current_user)
    if role == "none":
        raise HTTPException(status_code=403, detail="Forbidden")

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return [
        TaskStatus(
            id=t.id,
            status=t.status,
            result=t.result,
            title=t.title,
            description=t.description,
            assignee=t.assignee,
            project_id=t.project_id,
        )
        for t in tasks
    ]
