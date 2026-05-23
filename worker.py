import asyncio
import logging

from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal, Task as DbTask
from models import TaskState
from storage import queue

logger = logging.getLogger("task_app.worker")


async def worker() -> None:
    while True:
        task_id = await queue.get()
        logger.info("Worker processing task %s", task_id)
        task = None

        try:
            with SessionLocal() as db:
                task = db.get(DbTask, task_id)
                if not task:
                    logger.error("Task %s not found in database", task_id)
                    continue

                task.status = TaskState.processing.value
                db.commit()

                await asyncio.sleep(2)
                task.result = task.data.upper()
                task.status = TaskState.done.value
                db.commit()
                logger.info("Task %s completed", task_id)
        except Exception as err:
            logger.exception("Error processing task %s", task_id)
            try:
                if task is not None:
                    with SessionLocal() as db:
                        task = db.get(DbTask, task_id)
                        if task:
                            task.status = TaskState.error.value
                            db.commit()
            except SQLAlchemyError:
                logger.exception("Failed to update error status for task %s", task_id)
        finally:
            queue.task_done()
