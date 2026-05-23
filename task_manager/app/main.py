"""Main entry point for Task Manager with verification script."""
from database import SessionLocal, init_db
from models import TaskStatus
import crud


def main():
    """Run verification script for Task Manager."""
    # Initialize database
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        print("\n" + "="*50)
        print("TASK MANAGER VERIFICATION")
        print("="*50)
        
        # 1. Create 2 users
        print("\n1. Creating 2 users...")
        user1 = crud.create_user(db, username="alice", email="alice@example.com")
        print(f"   Created user: {user1.username} (id={user1.id})")
        
        user2 = crud.create_user(db, username="bob", email="bob@example.com")
        print(f"   Created user: {user2.username} (id={user2.id})")
        
        # 2. Create 2 projects
        print("\n2. Creating 2 projects...")
        project1 = crud.create_project(db, title="Website Redesign", description="Redesign company website")
        print(f"   Created project: {project1.title} (id={project1.id})")
        
        project2 = crud.create_project(db, title="Mobile App", description="Build mobile application")
        print(f"   Created project: {project2.title} (id={project2.id})")
        
        # 3. Create 5 tasks
        print("\n3. Creating 5 tasks...")
        task1 = crud.create_task(db, title="Design homepage", description="Create new homepage design", user_id=user1.id, project_id=project1.id)
        print(f"   Created task: {task1.title} (id={task1.id})")
        
        task2 = crud.create_task(db, title="Implement login", description="Add login functionality", user_id=user1.id, project_id=project1.id)
        print(f"   Created task: {task2.title} (id={task2.id})")
        
        task3 = crud.create_task(db, title="Setup CI/CD", description="Configure continuous integration", user_id=user2.id, project_id=project1.id)
        print(f"   Created task: {task3.title} (id={task3.id})")
        
        task4 = crud.create_task(db, title="Create API endpoints", description="Build REST API", user_id=user2.id, project_id=project2.id)
        print(f"   Created task: {task4.title} (id={task4.id})")
        
        task5 = crud.create_task(db, title="Write tests", description="Add unit tests", user_id=user1.id, project_id=project2.id)
        print(f"   Created task: {task5.title} (id={task5.id})")
        
        # 4. Tasks are already assigned to users via user_id
        print("\n4. Tasks assigned to users (via user_id)")
        
        # 5. Add comments
        print("\n5. Adding comments...")
        crud.add_comment(db, user_id=user1.id, task_id=task1.id, text="Started working on design")
        print(f"   Added comment to task '{task1.title}'")
        
        crud.add_comment(db, user_id=user2.id, task_id=task1.id, text="Looking good!")
        print(f"   Added comment to task '{task1.title}'")
        
        crud.add_comment(db, user_id=user1.id, task_id=task2.id, text="Need API specs")
        print(f"   Added comment to task '{task2.title}'")
        
        crud.add_comment(db, user_id=user2.id, task_id=task3.id, text="Pipeline configured")
        print(f"   Added comment to task '{task3.title}'")
        
        crud.add_comment(db, user_id=user1.id, task_id=task4.id, text="Will start tomorrow")
        print(f"   Added comment to task '{task4.title}'")
        
        crud.add_comment(db, user_id=user2.id, task_id=task5.id, text="Tests passing")
        print(f"   Added comment to task '{task5.title}'")
        
        # 6. Change task statuses
        print("\n6. Changing task statuses...")
        crud.change_task_status(db, task_id=task1.id, status=TaskStatus.IN_PROGRESS)
        print(f"   Task '{task1.title}' -> {TaskStatus.IN_PROGRESS.value}")
        
        crud.change_task_status(db, task_id=task2.id, status=TaskStatus.DONE)
        print(f"   Task '{task2.title}' -> {TaskStatus.DONE.value}")
        
        crud.change_task_status(db, task_id=task3.id, status=TaskStatus.IN_PROGRESS)
        print(f"   Task '{task3.title}' -> {TaskStatus.IN_PROGRESS.value}")
        
        crud.change_task_status(db, task_id=task4.id, status=TaskStatus.DONE)
        print(f"   Task '{task4.title}' -> {TaskStatus.DONE.value}")
        
        # 7. Get user tasks
        print("\n7. Tasks for user 'alice':")
        user_tasks = crud.get_user_tasks(db, user_id=user1.id)
        for t in user_tasks:
            status = t.status.value if hasattr(t.status, 'value') else t.status
            print(f"   - {t.title} [{status}]")
        
        # 8. Get project tasks
        print("\n8. Tasks for project 'Website Redesign':")
        project_tasks = crud.get_project_tasks(db, project_id=project1.id)
        for t in project_tasks:
            status = t.status.value if hasattr(t.status, 'value') else t.status
            print(f"   - {t.title} [{status}]")
        
        # 9. Get tasks count by status
        print("\n9. Tasks count by status:")
        status_counts = crud.get_tasks_count_by_status(db)
        for status, count in status_counts.items():
            print(f"   - {status}: {count}")
        
        # 10. Get last 5 user comments
        print("\n10. Last 5 comments by user 'alice':")
        comments = crud.get_last_user_comments(db, user_id=user1.id, limit=5)
        for c in comments:
            print(f"   - Task #{c.task_id}: {c.text}")
        
        print("\n" + "="*50)
        print("VERIFICATION COMPLETE!")
        print("="*50)
        
    except crud.NotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()