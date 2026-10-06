import os
from typing import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

load_dotenv()

# Shared State (Memory)
class AgentState(TypedDict):
    customer_name: str
    issue: str
    draft: str
    feedback: str
    iterations: int
    approved: bool

# LLM Configuration (Using OpenRouter)
llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model="google/gemini-2.5-flash",
    temperature=0.2,
    max_tokens=1000
)

# Pydantic Schema for the QA Manager's Evaluation
class QAEvaluation(BaseModel):
    approved: bool = Field(description="True if the draft is polite, empathetic, and resolves the issue.")
    feedback: str = Field(description="Specific feedback on what to change if not approved. Empty if approved.")

# Agent Nodes
def support_agent(state: AgentState):
    print(f"---[Support Agent] Drafting response (Iteration {state.get('iterations', 0) + 1})---")
    
    system_prompt = (
        "You are a customer support representative. Draft a polite, helpful reply to the customer's issue. "
        "If there is previous feedback from the QA Manager, you MUST incorporate it into this new draft."
    )
    
    user_prompt = (
        f"Customer Name: {state['customer_name']}\n"
        f"Issue: {state['issue']}\n"
        f"QA Manager Feedback: {state.get('feedback', 'None')}"
    )
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
    chain = prompt | llm
    
    response = chain.invoke({"input": user_prompt})
    
    return {
        "draft": response.content,
        "iterations": state.get("iterations", 0) + 1
    }

def qa_manager(state: AgentState):
    print("---[QA Manager] Reviewing draft---")
    
    system_prompt = (
        "You are a strict Customer Support QA Manager. "
        "Review the draft response. It MUST apologize for the inconvenience and offer a clear next step. "
        "If it fails to do so, reject it and provide feedback."
    )
    
    user_prompt = (
        f"Customer Issue: {state['issue']}\n"
        f"Proposed Draft:\n{state['draft']}"
    )
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
    structured_llm = llm.with_structured_output(QAEvaluation)
    chain = prompt | structured_llm
    
    evaluation = chain.invoke({"input": user_prompt})
    
    if evaluation.approved:
        print("---[QA Manager] Approved!✅---")
    else:
        print(f"---[QA Manager] Rejected!❌ Feedback: {evaluation.feedback}---")
        
    return {
        "approved": evaluation.approved,
        "feedback": evaluation.feedback
    }

# 5. Routing Logic
def route_evaluation(state: AgentState):
    if state["approved"]:
        return "end"
    if state["iterations"] >= 3:
        print("---[System] Max iterations reached, forcing approval.---")
        return "end"
    return "rewrite"

# 6. Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("drafter", support_agent)
workflow.add_node("qa", qa_manager)

workflow.set_entry_point("drafter")
workflow.add_edge("drafter", "qa")
workflow.add_conditional_edges(
    "qa",
    route_evaluation,
    {
        "end": END,
        "rewrite": "drafter"
    }
)

agent_workflow = workflow.compile()

# 7. Local Testing Block (Runs only if this file is executed directly)
if __name__ == "__main__":
    initial_state = {
        "customer_name": "Charlie",
        "issue": "I want a refund, your app crashed and deleted my work.",
        "iterations": 0
    }
    
    print("Starting Multi-Agent Debate...\n")
    final_state = agent_workflow.invoke(initial_state)
    
    print("\n=== FINAL APPROVED RESPONSE ===")
    print(final_state["draft"])