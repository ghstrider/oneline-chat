# PRD Agent - Product Requirements Document Specialist

## Overview
The PRD Agent is a specialized AI agent focused on creating comprehensive product specifications and technical requirements. It helps translate business requirements into detailed product and technical specifications.

## Features
- Product vision and strategy definition
- Technical requirements specification
- User experience documentation
- API and data model specifications
- Release planning and MVP definition
- Feature prioritization and roadmapping

## Installation

1. Navigate to the agent directory:
```bash
cd agents/prd_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install MCP tools (requires Node.js):
```bash
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @mettamatt/code-reasoning
npm install -g @wonderwhy-er/desktop-commander
```

## Running the Agent

### HTTP Server Mode (Default)
Run the agent as an HTTP server on port 8002:
```bash
python prd_agent.py
```

### CLI Mode
Run the agent in interactive CLI mode:
```bash
python prd_agent.py cli
```

## API Endpoints

### POST /query
Send queries to the PRD agent:
```bash
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Help me create a PRD for a mobile app feature"}'
```

### GET /health
Check agent health status:
```bash
curl http://localhost:8002/health
```

### GET /
Get agent information:
```bash
curl http://localhost:8002/
```

## Access via Caddy Gateway
When Caddy is running, access the agent at:
```
http://localhost:9000/prd
```

## Configuration
- **Model**: Uses OpenAI GPT-4o by default
- **Port**: 8002
- **MCP Tools**: Python execution, code reasoning, desktop commander, filesystem access

## Example Use Cases
- Creating detailed PRD documents
- Defining technical specifications
- API design and documentation
- User persona and journey mapping
- MVP scope definition
- Feature specification with acceptance criteria
- System architecture documentation
- Performance and scalability requirements