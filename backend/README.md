# Oneline Chat Backend

OpenAI-compatible streaming chat API with PostgreSQL persistence.

## Features

- **OpenAI-compatible API** - Drop-in replacement for OpenAI chat completions
- **Streaming & Non-streaming** - Real-time SSE streaming and traditional responses
- **Multiple AI providers** - Support for OpenAI and Ollama (local LLM)
- **PostgreSQL persistence** - Chat history with SQLModel/Pydantic
- **Production ready** - Docker deployment, health checks, structured logging
- **Comprehensive testing** - 17 integration tests, 71%+ coverage

## Quick Start

### 1. Prerequisites
- Python 3.11+
- PostgreSQL running locally
- Ollama installed (optional, for local LLM)

### 2. Installation
```bash
# Install in development mode
pip install -e ".[dev]"

# Or use make
make dev
```

### 3. Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
```

### 4. Database Setup
```bash
# Create database tables
make db-create

# Or manually
python -c "from oneline_chat.db import create_db_and_tables; create_db_and_tables()"
```

### 5. Running the Application

**Development Mode:**
```bash
# Using VS Code: F5 -> "FastAPI - Development"
# Or command line:
make run
# Or directly:
uvicorn oneline_chat.app:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode:**
```bash
make run-prod
# Or:
python -m oneline_chat.main
```

## VS Code Integration

### Launch Configurations
Press `F5` and select from:
- **FastAPI - Development** - Run with auto-reload and debug logging
- **FastAPI - Production** - Run in production mode
- **FastAPI - OpenAI Mode** - Run with OpenAI provider
- **Run All Tests** - Execute all test suites
- **Run Integration Tests** - Execute only integration tests
- **Debug Current Test File** - Debug the currently open test file

### Testing with HTTP Files
Open `oneline_chat.http` in VS Code with REST Client extension:
- Health checks
- Chat completions (streaming & non-streaming)
- Multi-turn conversations
- Error handling tests
- Performance tests

## Development Commands

### Testing
```bash
# Run all integration tests
make test-integration
./run_tests.sh

# Run all tests
make test-all

# Run with coverage
make coverage

# Run specific test file
pytest tests/test_chat_router.py -v
```

### Code Quality
```bash
# Format, lint, and type check
make check

# Individual commands
make format    # Black formatting
make lint      # Ruff linting
make type-check # MyPy type checking
```

### Database Operations
```bash
make db-create    # Create tables
make db-reset     # Drop and recreate schema
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with environment info |
| `/` | GET | Root endpoint with API information |
| `/api/v1/models` | GET | List available models (OpenAI compatible) |
| `/api/v1/chat/completions` | POST | Chat completions (streaming/non-streaming) |
| `/api/v1/chat/stream` | POST | Explicit streaming endpoint |
| `/api/v1/chat/history/{chat_id}` | GET | Retrieve chat conversation history |

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Application
APP_ENV=development          # development, staging, production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=oneline_chat_app

# AI Provider
AI_PROVIDER=ollama          # 'ollama' or 'openai'

# Ollama (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-r1:8b

# OpenAI (if using OpenAI)
OPENAI_API_KEY=your-openai-api-key-here
```

### Ollama Setup (Local LLM)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
make pull-model
# Or: ollama pull deepseek-r1:8b

# Start Ollama server
make serve-ollama
# Or: ollama serve
```

## Docker Deployment

### Single Container
```bash
# Build image
make docker-build
# Or: docker build -t oneline-chat .

# Run container
docker run -p 8000:8000 \
  -e AI_PROVIDER=ollama \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434/v1 \
  oneline-chat
```

### Full Stack with Docker Compose
```bash
# Start PostgreSQL + API
make docker-up
# Or: docker-compose up -d

# View logs
make docker-logs

# Stop services
make docker-down
```

## Testing

### Test Structure
```
tests/
├── test_integration_local.py  # Database repository tests
└── test_chat_router.py        # API endpoint tests
```

### Running Tests
```bash
# All integration tests (recommended)
make test-integration

# Specific test file
pytest tests/test_chat_router.py -v --no-cov

# With coverage report
make coverage

# Using VS Code: F5 -> "Run Integration Tests"
```

### Test Database
Tests use a separate `test_db` database that's automatically created and cleaned up.

## API Usage Examples

### Basic Chat Completion
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:8b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

### Streaming Response
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "deepseek-r1:8b",
    "messages": [{"role": "user", "content": "Write a poem"}],
    "stream": true
  }'
```

## Project Structure

```
oneline-chat/backend/
├── src/oneline_chat/           # Main package
│   ├── core/                   # Configuration & logging
│   ├── db/                     # Database models & operations
│   ├── services/               # External service integrations
│   ├── api/                    # FastAPI routers
│   ├── app.py                  # FastAPI application
│   └── main.py                 # CLI entry point
├── tests/                      # Test suite
├── .vscode/launch.json         # VS Code debug configurations
├── oneline_chat.http           # HTTP client test requests
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Full stack deployment
├── Makefile                    # Development commands
└── run_tests.sh               # Integration test script
```

## Troubleshooting

### Common Issues

**PostgreSQL Connection Failed:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Create database if missing
createdb oneline_chat_app
```

**Ollama Connection Failed:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if missing
ollama pull deepseek-r1:8b
```

**Import Errors:**
```bash
# Reinstall package
pip install -e .
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Run `make check` before committing
4. Update documentation as needed

## License

MIT License