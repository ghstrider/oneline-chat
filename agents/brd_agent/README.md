# BRD Agent - Business Requirements Document Specialist

## Overview
The BRD Agent is a specialized AI agent focused on gathering, analyzing, and documenting business requirements. It helps create comprehensive Business Requirements Documents with clear structure and alignment to business objectives.

## Features
- Requirements gathering and elicitation
- Business process analysis
- Stakeholder management
- Documentation with SMART criteria
- MoSCoW prioritization
- Requirement traceability

## Installation

1. Navigate to the agent directory:
```bash
cd agents/brd_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install MCP tools (requires Node.js):
```bash
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @mettamatt/code-reasoning
```

## Running the Agent

### HTTP Server Mode (Default)
Run the agent as an HTTP server on port 8001:
```bash
python brd_agent.py
```

### CLI Mode
Run the agent in interactive CLI mode:
```bash
python brd_agent.py cli
```

## API Endpoints

### POST /query
Send queries to the BRD agent:
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Help me create a BRD for a new e-commerce feature"}'
```

### GET /health
Check agent health status:
```bash
curl http://localhost:8001/health
```

### GET /
Get agent information:
```bash
curl http://localhost:8001/
```

## Access via Caddy Gateway
When Caddy is running, access the agent at:
```
http://localhost:9000/brd
```

## Configuration
- **Model**: Uses OpenAI GPT-4o by default
- **Port**: 8001
- **MCP Tools**: Python execution, code reasoning, filesystem access

## Example Use Cases
- Creating comprehensive BRD documents
- Gathering and analyzing business requirements
- Defining success criteria and KPIs
- User story documentation
- Stakeholder requirement validation
- Business process mapping