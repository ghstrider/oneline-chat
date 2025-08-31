import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider

# Configure models
ollama_model = OpenAIModel(
    model_name="incept5/llama3.1-claude",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)

openai_model = OpenAIModel("gpt-4o")

# BRD Agent specific instructions
instructions = """
You are a specialized Business Requirements Document (BRD) agent focused on gathering, analyzing, and documenting business requirements.

## Core Responsibilities:

1. **Requirements Gathering:**
   - Elicit business needs and objectives from stakeholders
   - Identify key business problems to be solved
   - Define success criteria and KPIs
   - Document user stories and use cases

2. **Business Analysis:**
   - Analyze current business processes and workflows
   - Identify gaps and opportunities for improvement
   - Define business rules and constraints
   - Map stakeholder needs to business objectives

3. **Documentation Standards:**
   - Create comprehensive BRD documents with clear structure
   - Include executive summary, business context, and objectives
   - Define scope, assumptions, and dependencies
   - Document functional and non-functional requirements
   - Provide acceptance criteria for each requirement

4. **Stakeholder Management:**
   - Facilitate requirement validation sessions
   - Ensure alignment between different stakeholder groups
   - Manage requirement changes and impact analysis
   - Maintain requirement traceability matrix

5. **Best Practices:**
   - Use SMART criteria for objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
   - Apply MoSCoW prioritization (Must have, Should have, Could have, Won't have)
   - Ensure requirements are testable and measurable
   - Focus on business value and ROI
"""

# MCP Tools configuration
run_python = MCPServerStdio(
    "deno",
    args=[
        "run",
        "-N",
        "-R=node_modules",
        "-W=node_modules",
        "--node-modules-dir=auto",
        "jsr:@pydantic/mcp-run-python",
        "stdio",
    ],
)

code_reasoning = MCPServerStdio(
    command="npx",
    args=["-y", "@mettamatt/code-reasoning"],
    tool_prefix="code_reasoning",
)

filesystem = MCPServerStdio(
    command="npx",
    args=[
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/ankushsingh/Desktop",
        "/Users/ankushsingh/Downloads",
    ],
)

# Initialize agent
agent = Agent(
    instructions=instructions,
    model=openai_model,
    toolsets=[
        run_python,
        code_reasoning,
        filesystem,
    ],
)

# FastAPI app
app = FastAPI(title="BRD Agent API", version="1.0.0")

class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None

class QueryResponse(BaseModel):
    response: str
    metadata: Optional[dict] = None

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Process a query through the BRD agent
    """
    try:
        result = await agent.run(request.query)
        # Extract the response content from the result object
        response_text = str(result) if hasattr(result, '__str__') else str(result)
        
        return QueryResponse(
            response=response_text,
            metadata={"agent": "brd", "model": "gpt-4o"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "agent": "brd"}

@app.get("/")
async def root():
    """
    Root endpoint with agent information
    """
    return {
        "agent": "BRD Agent",
        "description": "Business Requirements Document specialist",
        "endpoints": {
            "query": "/query",
            "health": "/health"
        }
    }

async def run_cli():
    """Run in CLI mode"""
    async with agent:
        await agent.to_cli()

async def run_server():
    """Run as HTTP server"""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        asyncio.run(run_cli())
    else:
        asyncio.run(run_server())