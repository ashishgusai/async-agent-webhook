import time
from celery import Celery

# Import our LangGraph workflow and DB tools
from agents import agent_workflow
import db

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
    print(f"[{ticket_id}] CELERY WORKER: Kicking off Multi-Agent Debate...")
   
    # Prepare initial state for the LangGraph
    initial_state = {
        "customer_name": ticket_data.get("customer_name"),
        "issue": ticket_data.get("issue_description"),
        "iterations": 0
    }

    # Invoke the graph (this is a blocking API call, but runs safely in the background)
    final_state = agent_workflow.invoke(initial_state)

    print(f"[{ticket_id}] CELERY WORKER: Debate complete after {final_state['iterations']} iterations.")
    
    # Save the approved draft to SQLite
    db.update_ticket_resolution(
        ticket_id=ticket_id,
        draft=final_state["draft"],
        iterations=final_state["iterations"]
    )

    return {"status": "success", "ticket_id": ticket_id}