"""CRUD operation tests for Task Manager Pro."""

import pytest
from app import crud_pro
from app.schemas_pro import UserCreate, ProjectCreate, TaskCreate, CommentCreate, TagCreate


class TestUserCRUD:
    """User CRUD tests."""
    
    def test_create_user(self, db_session, test_user_data):
        """Test creating a user."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        assert user.id is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.role.value == test_user_data["role"]
    
    def test_create_duplicate_user_email(self, db_session, test_user_data):
        """Test creating duplicate user by email."""
        user_create = UserCreate(**test_user_data)
        crud_pro.create_user(db_session, user_create)
        
        with pytest.raises(ValueError):
            crud_pro.create_user(db_session, user_create)
    
    def test_get_user(self, db_session, test_user_data):
        """Test getting a user."""
        user_create = UserCreate(**test_user_data)
        created_user = crud_pro.create_user(db_session, user_create)
        
        user = crud_pro.get_user(db_session, created_user.id)
        assert user.id == created_user.id
        assert user.email == test_user_data["email"]
    
    def test_get_user_by_email(self, db_session, test_user_data):
        """Test getting user by email."""
        user_create = UserCreate(**test_user_data)
        crud_pro.create_user(db_session, user_create)
        
        user = crud_pro.get_user_by_email(db_session, test_user_data["email"])
        assert user is not None
        assert user.email == test_user_data["email"]
    
    def test_get_user_by_username(self, db_session, test_user_data):
        """Test getting user by username."""
        user_create = UserCreate(**test_user_data)
        crud_pro.create_user(db_session, user_create)
        
        user = crud_pro.get_user_by_username(db_session, test_user_data["username"])
        assert user is not None
        assert user.username == test_user_data["username"]
    
    def test_get_users_pagination(self, db_session, test_user_data):
        """Test getting users with pagination."""
        for i in range(5):
            data = test_user_data.copy()
            data["username"] = f"user{i}"
            data["email"] = f"user{i}@example.com"
            user_create = UserCreate(**data)
            crud_pro.create_user(db_session, user_create)
        
        users, total = crud_pro.get_users(db_session, skip=0, limit=3)
        assert len(users) == 3
        assert total == 5
    
    def test_update_user(self, db_session, test_user_data):
        """Test updating a user."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        from app.schemas_pro import UserUpdate
        update_data = UserUpdate(username="newusername")
        updated_user = crud_pro.update_user(db_session, user.id, update_data)
        
        assert updated_user.username == "newusername"
    
    def test_delete_user(self, db_session, test_user_data):
        """Test deleting a user."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        success = crud_pro.delete_user(db_session, user.id)
        assert success is True
        
        deleted_user = crud_pro.get_user(db_session, user.id)
        assert deleted_user.is_active is False


class TestProjectCRUD:
    """Project CRUD tests."""
    
    def test_create_project(self, db_session, test_user_data, test_project_data):
        """Test creating a project."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        assert project.id is not None
        assert project.title == test_project_data["title"]
        assert project.owner_id == user.id
    
    def test_get_project(self, db_session, test_user_data, test_project_data):
        """Test getting a project."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        created_project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        project = crud_pro.get_project(db_session, created_project.id)
        assert project.id == created_project.id
        assert project.title == test_project_data["title"]
    
    def test_update_project(self, db_session, test_user_data, test_project_data):
        """Test updating a project."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        from app.schemas_pro import ProjectUpdate
        update_data = ProjectUpdate(title="Updated Title")
        updated_project = crud_pro.update_project(db_session, project.id, update_data, user_id=user.id)
        
        assert updated_project.title == "Updated Title"
    
    def test_delete_project(self, db_session, test_user_data, test_project_data):
        """Test deleting a project."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        success = crud_pro.delete_project(db_session, project.id, user_id=user.id)
        assert success is True
    
    def test_add_project_member(self, db_session, test_user_data, test_project_data):
        """Test adding project member."""
        user_create = UserCreate(**test_user_data)
        user1 = crud_pro.create_user(db_session, user_create)
        
        data = test_user_data.copy()
        data["username"] = "user2"
        data["email"] = "user2@example.com"
        user_create2 = UserCreate(**data)
        user2 = crud_pro.create_user(db_session, user_create2)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user1.id)
        
        success = crud_pro.add_project_member(db_session, project.id, user2.id, actor_id=user1.id)
        assert success is True
        
        # Verify member was added
        updated_project = crud_pro.get_project(db_session, project.id)
        assert user2 in updated_project.members


class TestTaskCRUD:
    """Task CRUD tests."""
    
    def test_create_task(self, db_session, test_user_data, test_project_data, test_task_data):
        """Test creating a task."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        assert task.id is not None
        assert task.project_id == project.id
        assert task.title == test_task_data["title"]
    
    def test_get_task(self, db_session, test_user_data, test_project_data, test_task_data):
        """Test getting a task."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        created_task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        task = crud_pro.get_task(db_session, created_task.id)
        assert task.id == created_task.id
        assert task.title == test_task_data["title"]
    
    def test_update_task(self, db_session, test_user_data, test_project_data, test_task_data):
        """Test updating a task."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        from app.schemas_pro import TaskUpdate
        update_data = TaskUpdate(status="in_progress")
        updated_task = crud_pro.update_task(db_session, task.id, update_data, user_id=user.id)
        
        assert updated_task.status.value == "in_progress"
    
    def test_delete_task(self, db_session, test_user_data, test_project_data, test_task_data):
        """Test deleting a task."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        success = crud_pro.delete_task(db_session, task.id, user_id=user.id)
        assert success is True


class TestCommentCRUD:
    """Comment CRUD tests."""
    
    def test_create_comment(self, db_session, test_user_data, test_project_data, test_task_data, test_comment_data):
        """Test creating a comment."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        comment_create = CommentCreate(**test_comment_data)
        comment = crud_pro.create_comment(db_session, task.id, user.id, comment_create)
        
        assert comment.id is not None
        assert comment.task_id == task.id
        assert comment.content == test_comment_data["content"]
    
    def test_get_comment(self, db_session, test_user_data, test_project_data, test_task_data, test_comment_data):
        """Test getting a comment."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        comment_create = CommentCreate(**test_comment_data)
        created_comment = crud_pro.create_comment(db_session, task.id, user.id, comment_create)
        
        comment = crud_pro.get_comment(db_session, created_comment.id)
        assert comment.id == created_comment.id
    
    def test_delete_comment(self, db_session, test_user_data, test_project_data, test_task_data, test_comment_data):
        """Test deleting a comment."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        project_create = ProjectCreate(**test_project_data)
        project = crud_pro.create_project(db_session, project_create, owner_id=user.id)
        
        task_create = TaskCreate(project_id=project.id, **test_task_data)
        task = crud_pro.create_task(db_session, task_create, creator_id=user.id)
        
        comment_create = CommentCreate(**test_comment_data)
        comment = crud_pro.create_comment(db_session, task.id, user.id, comment_create)
        
        success = crud_pro.delete_comment(db_session, comment.id, user_id=user.id)
        assert success is True


class TestTagCRUD:
    """Tag CRUD tests."""
    
    def test_create_tag(self, db_session, test_tag_data):
        """Test creating a tag."""
        tag_create = TagCreate(**test_tag_data)
        tag = crud_pro.create_tag(db_session, tag_create)
        
        assert tag.id is not None
        assert tag.name == test_tag_data["name"]
    
    def test_get_tag(self, db_session, test_tag_data):
        """Test getting a tag."""
        tag_create = TagCreate(**test_tag_data)
        created_tag = crud_pro.create_tag(db_session, tag_create)
        
        tag = crud_pro.get_tag(db_session, created_tag.id)
        assert tag.id == created_tag.id
        assert tag.name == test_tag_data["name"]
    
    def test_delete_tag(self, db_session, test_tag_data):
        """Test deleting a tag."""
        tag_create = TagCreate(**test_tag_data)
        tag = crud_pro.create_tag(db_session, tag_create)
        
        success = crud_pro.delete_tag(db_session, tag.id)
        assert success is True


class TestAuditLogs:
    """Audit log tests."""
    
    def test_audit_log_on_create(self, db_session, test_user_data):
        """Test audit log creation."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        logs, total = crud_pro.get_audit_logs(db_session, entity_type="user", entity_id=user.id)
        assert total > 0
        assert any(log.action == "create" for log in logs)
    
    def test_audit_log_on_update(self, db_session, test_user_data):
        """Test audit log on update."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        from app.schemas_pro import UserUpdate
        update_data = UserUpdate(username="newusername")
        crud_pro.update_user(db_session, user.id, update_data)
        
        logs, total = crud_pro.get_audit_logs(db_session, entity_type="user", entity_id=user.id)
        assert any(log.action == "update" for log in logs)
    
    def test_audit_log_on_delete(self, db_session, test_user_data):
        """Test audit log on delete."""
        user_create = UserCreate(**test_user_data)
        user = crud_pro.create_user(db_session, user_create)
        
        crud_pro.delete_user(db_session, user.id)
        
        logs, total = crud_pro.get_audit_logs(db_session, entity_type="user", entity_id=user.id)
        assert any(log.action == "delete" for log in logs)
