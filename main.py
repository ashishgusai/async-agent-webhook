# main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
import uuid

app = FastAPI(
    title="Async Multi-Agent Webhook",
    description="Processes incoming support tickets using background AI agents.",
    version="0.1.0"
)

# Pydantic Models for Webhook Payload
class TicketPayload(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_name: str
    issue_description: str
    priority: str = Field(default="normal")

class WebhookResponse(BaseModel):
    message: str
    ticket_id: str
    status: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook/support-ticket", response_model=WebhookResponse, status_code=202)
async def receive_ticket(payload: TicketPayload):
    """
    Receives a webhook payload from a customer support system (e.g., Zendesk).
    Immediately returns a 202 Accepted to prevent timeouts.
    """
    
    print(f"[{payload.ticket_id}] Received ticket from {payload.customer_name}: {payload.priority} priority.")
    
    return WebhookResponse(
        message="Webhook received. AI agents are processing the ticket in the background.",
        ticket_id=payload.ticket_id,
        status="processing"
    )