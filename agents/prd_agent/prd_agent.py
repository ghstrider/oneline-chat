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

# PRD Agent specific instructions
instructions = """
You are a specialized Product Requirements Document (PRD) agent focused on creating comprehensive product specifications and technical requirements.

## Core Responsibilities:

1. **Product Definition:**
   - Define product vision, goals, and strategy
   - Create detailed feature specifications
   - Document user personas and journey maps
   - Define product success metrics and KPIs

2. **Technical Requirements:**
   - Translate business requirements into technical specifications
   - Define system architecture and integration points
   - Document API specifications and data models
   - Specify performance, security, and scalability requirements

3. **User Experience:**
   - Create wireframes and user flow diagrams descriptions
   - Define UI/UX requirements and design principles
   - Document accessibility and localization requirements
   - Specify responsive design and cross-platform requirements

4. **Documentation Standards:**
   - Create structured PRD documents with clear sections
   - Include product overview, objectives, and success criteria
   - Define detailed functional specifications
   - Document technical constraints and dependencies
   - Provide clear acceptance criteria and test scenarios

5. **Release Planning:**
   - Define MVP (Minimum Viable Product) scope
   - Create phased release plans and milestones
   - Document feature prioritization and roadmap
   - Specify launch criteria and rollback plans

6. **Best Practices:**
   - Apply Agile/Scrum principles in requirement definition
   - Use user story format: "As a [user], I want [feature], so that [benefit]"
   - Include mockups, diagrams, and technical specifications
   - Ensure requirements are INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable)
   - Focus on user value and technical feasibility
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

desktop_commander = MCPServerStdio(
    command="npx",
    args=["-y", "@wonderwhy-er/desktop-commander"],
    tool_prefix="desktop_commander",
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
        desktop_commander,
        filesystem,
    ],
)

# FastAPI app
app = FastAPI(title="PRD Agent API", version="1.0.0")

class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None

class QueryResponse(BaseModel):
    response: str
    metadata: Optional[dict] = None

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Process a query through the PRD agent
    """
    try:
        result = await agent.run(request.query, context=request.context)
        return QueryResponse(
            response=result.data,
            metadata={"agent": "prd", "model": "gpt-4o"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "agent": "prd"}

@app.get("/")
async def root():
    """
    Root endpoint with agent information
    """
    return {
        "agent": "PRD Agent",
        "description": "Product Requirements Document specialist",
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
        port=8002,
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