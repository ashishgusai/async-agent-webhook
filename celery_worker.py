import time
from celery import Celery

# Initialize Celery app
# Broker: Where messages are sent (Redis)
# Backend: Where results are stored (Redis)
celery_app = Celery(
    "agent_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="process_ticket_task")
def process_ticket_task(ticket_data: dict):
    """
    This runs in the background outside of the FastAPI event loop.
    """
    ticket_id = ticket_data.get("ticket_id")
    customer = ticket_data.get("customer_name")
    
    print(f"[{ticket_id}] CELERY WORKER: Starting AI processing for {customer}...")
    
    # Simulate an LLM taking 5 seconds to process
    time.sleep(5)
    
    print(f"[{ticket_id}] CELERY WORKER: Processing complete.")
    
    return {"status": "success", "ticket_id": ticket_id, "resolution": "Simulated resolution"}