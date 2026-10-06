from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uuid

import db
# Import our Celery task
from celery_worker import process_ticket_task

# Initialize SQLite database on API startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield

app = FastAPI(
    title="Async Multi-Agent Webhook",
    description="Processes incoming support tickets using background AI agents.",
    version="1.0.0",
    lifespan=lifespan
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
    # Save initial 'processing' state to database
    db.insert_ticket(payload.ticket_id, payload.customer_name, payload.issue_description)
    
    # Dispatch to Celery worker in the background
    process_ticket_task.delay(payload.model_dump())
    
    # Return 202 Accepted immediately
    return WebhookResponse(
        message="Webhook received. AI agents are processing the ticket in the background.",
        ticket_id=payload.ticket_id,
        status="queued"
    )

# Endpoint to check the status of a ticket
@app.get("/api/v1/tickets/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    record = db.get_ticket(ticket_id)
    if not record:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return dict(record)