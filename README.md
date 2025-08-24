# Oneline Chat

A modern, real-time streaming chat application built with FastAPI (Python) backend and React TypeScript frontend.

## 🏗️ Project Structure

```
oneline-chat/
├── backend/          # FastAPI Python backend
│   ├── src/         # Source code
│   ├── tests/       # Test files
│   └── requirements.txt
├── ui/              # React TypeScript frontend
│   ├── src/         # Source code
│   └── package.json
├── docker-compose.yml
└── README.md
```

## ✨ Features

### Backend (FastAPI + Python)
- 🔄 **Real-time streaming chat** via Server-Sent Events (SSE)
- 🤖 **AI Integration** with OpenAI/Ollama support
- 🗄️ **PostgreSQL database** with SQLModel ORM
- 🔧 **Configurable settings** via environment variables
- 📝 **Comprehensive logging** and error handling
- 🧪 **Full test coverage** with pytest

### Frontend (React + TypeScript)
- 💬 **Modern chat interface** with real-time streaming
- 🌓 **Dark/light mode** support
- 📱 **Responsive design** with Tailwind CSS
- ⚙️ **Chat settings** (model selection, temperature, etc.)
- 📡 **Axios HTTP client** with interceptors
- 🔧 **Configurable API endpoints** via environment variables

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- npm/yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m oneline_chat.main
```

### Frontend Setup
```bash
cd ui
npm install
npm run dev
```

### Environment Variables

**Backend** (`.env` in `/backend`):
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=oneline_chat_app
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-r1:8b
```

**Frontend** (`.env` in `/ui`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

## 🐳 Docker Setup

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- FastAPI backend
- React frontend
- Nginx reverse proxy

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints
- `POST /api/v1/chat/stream` - Streaming chat endpoint
- `POST /api/v1/chat/completions` - Non-streaming chat
- `GET /api/v1/chat/history/{chat_id}` - Chat history
- `GET /api/v1/models` - Available models

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
pytest  # Run tests
python -m oneline_chat.main  # Start server
```

### Frontend Development
```bash
cd ui
npm install
npm run dev     # Start dev server
npm run build   # Build for production
npm run lint    # Run linting
```

## 🏛️ Architecture

### Backend Stack
- **FastAPI** - Modern Python web framework
- **SQLModel** - SQLAlchemy + Pydantic for database ORM
- **PostgreSQL** - Primary database
- **Pydantic Settings** - Configuration management
- **Uvicorn** - ASGI server

### Frontend Stack
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client with interceptors

### Communication
- **REST API** for standard operations
- **Server-Sent Events (SSE)** for real-time streaming
- **JSON** for data exchange

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov  # With coverage
```

### Frontend Tests
```bash
cd ui
npm test
```

## 📦 Deployment

### Production Build
```bash
# Backend
cd backend
pip install -r requirements.txt
python -m oneline_chat.main

# Frontend
cd ui
npm install
npm run build
npm run preview
```

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔧 Configuration

### Chat Modes
- **Single**: Single AI agent responds
- **Multiple**: Multiple AI agents can participate

### Supported Models
- DeepSeek R1 8B (default)
- GPT-3.5 Turbo
- GPT-4
- Claude 3 Haiku/Sonnet

### Settings
- **Temperature**: 0.0-2.0 (creativity level)
- **Max Tokens**: 50-4000 (response length)
- **Save to DB**: Toggle conversation persistence