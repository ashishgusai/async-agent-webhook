from fastapi import FastAPI
from pydantic import BaseModel, Field
import uuid

# Import our Celery task
from celery_worker import process_ticket_task

app = FastAPI(
    title="Async Multi-Agent Webhook",
    description="Processes incoming support tickets using background AI agents.",
    version="0.2.0"
)

class TicketPayload(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    issue_description: str
    priority: str = Field(default="normal")

class WebhookResponse(BaseModel):
    message: str
    ticket_id: str
    status: str

@app.post("/webhook/support-ticket", response_model=WebhookResponse, status_code=202)
async def receive_ticket(payload: TicketPayload):
    # 1. Convert Pydantic model to a standard dictionary for Celery serialization
    ticket_dict = payload.model_dump()
    
    # 2. Dispatch to Celery queue immediately
    # .delay() pushes the job to Redis and returns instantly
    process_ticket_task.delay(ticket_dict)
    
    # 3. Return HTTP 202 to the third-party webhook sender
    return WebhookResponse(
        message="Webhook received. AI agents are processing the ticket in the background.",
        ticket_id=payload.ticket_id,
        status="queued"
    )