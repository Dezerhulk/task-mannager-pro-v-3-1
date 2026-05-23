from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, constr


class TaskState(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"
    canceled = "canceled"


class LoginRequest(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=10, max_length=128)


class RegisterRequest(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=10, max_length=128)
    email: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    username: str
    role: str


class ProjectCreate(BaseModel):
    title: constr(min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=1200)


class ProjectSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    owner: str
    role: str


class ProjectTaskCreate(BaseModel):
    title: constr(min_length=3, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    assignee: Optional[str] = None


class TaskStatus(BaseModel):
    id: str
    status: TaskState
    result: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    project_id: Optional[str] = None


class TaskCreate(BaseModel):
    data: str = Field(..., min_length=1, max_length=1000)
