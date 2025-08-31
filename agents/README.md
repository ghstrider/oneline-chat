# Multi-Agent System

## Overview
This directory contains specialized AI agents for different business and product documentation needs. Each agent runs as an independent service and can be accessed via HTTP API or CLI.

## Architecture
```
agents/
├── brd_agent/          # Business Requirements Document Agent (Port 8001)
├── prd_agent/          # Product Requirements Document Agent (Port 8002)
├── Caddyfile          # Reverse proxy configuration
└── README.md          # This file
```

## Quick Start

### 1. Start Individual Agents

#### Terminal 1: Start BRD Agent
```bash
cd agents/brd_agent
pip install -r requirements.txt
python brd_agent.py
```

#### Terminal 2: Start PRD Agent
```bash
cd agents/prd_agent
pip install -r requirements.txt
python prd_agent.py
```

### 2. Start Caddy Gateway (Optional)
```bash
cd agents
caddy run
```

## Access Points

### Direct Access
- BRD Agent: `http://localhost:8001`
- PRD Agent: `http://localhost:8002`

### Via Caddy Gateway
- BRD Agent: `http://localhost:9000/brd`
- PRD Agent: `http://localhost:9000/prd`
- Gateway Health: `http://localhost:9000/health`

## API Usage Examples

### Query BRD Agent
```bash
curl -X POST http://localhost:9000/brd/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a BRD for user authentication feature"}'
```

### Query PRD Agent
```bash
curl -X POST http://localhost:9000/prd/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create technical specs for a REST API"}'
```

## Agent Capabilities

### BRD Agent
- Business requirements gathering
- Stakeholder analysis
- Success criteria definition
- Business process documentation
- Requirement prioritization (MoSCoW)

### PRD Agent
- Product specification
- Technical requirements
- API documentation
- User experience design
- Release planning
- Feature roadmapping

## Adding New Agents

1. Create a new directory: `agents/new_agent/`
2. Copy the structure from existing agents
3. Modify the instructions and port number
4. Update the Caddyfile with new routing rules
5. Create agent-specific README

## Prerequisites

- Python 3.8+
- Node.js (for MCP tools)
- Caddy server (for gateway)
- OpenAI API key (set as environment variable)

## Environment Variables

```bash
export OPENAI_API_KEY="your-api-key"
```

## Deployment Notes

Each agent is independently deployable:
- Separate requirements.txt for isolation
- Individual port assignments
- Independent MCP tool configurations
- Can run standalone or behind gateway

## Troubleshooting

1. **Port Already in Use**: Change port in agent's `run_server()` function
2. **MCP Tools Not Found**: Install required npm packages
3. **API Key Missing**: Set OPENAI_API_KEY environment variable
4. **Caddy Not Running**: Install Caddy from https://caddyserver.com/

## Development

To run agents in CLI mode for testing:
```bash
python brd_agent.py cli
python prd_agent.py cli
```

## License
[Your License Here]