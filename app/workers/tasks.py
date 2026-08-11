from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.process_request_task")
def process_request_task(request_id: int) -> None:
    from app.core.database import SessionLocal
    from app.services.ai.pipeline import run_request_pipeline

    db = SessionLocal()
    try:
        run_request_pipeline(db, request_id)
    finally:
        db.close()
