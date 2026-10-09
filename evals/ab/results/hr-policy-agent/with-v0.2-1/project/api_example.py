#!/usr/bin/env python3
"""
Optional: Simple FastAPI example for running the HR agent as a web service.

This shows how to wrap the agent in a REST API.
Install: pip install fastapi uvicorn

Run: uvicorn api_example:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel
import agent

app = FastAPI(title="HR Policy Agent API", version="1.0.0")

# Pre-load policies at startup
policies = agent.load_policies()


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "HR Policy Agent API running"}


@app.get("/policies")
def list_policies():
    """List available policies."""
    return {
        "policies": list(policies.keys()),
        "count": len(policies)
    }


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """Ask a question about HR policies."""
    answer = agent.run_agent_loop(request.question, policies)
    return AnswerResponse(question=request.question, answer=answer)


@app.get("/policy/{policy_name}")
def get_policy(policy_name: str):
    """Get the full content of a specific policy."""
    if policy_name not in policies:
        return {"error": f"Policy '{policy_name}' not found"}
    return {
        "name": policy_name,
        "content": policies[policy_name]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
