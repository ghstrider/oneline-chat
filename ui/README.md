# Oneline Chat UI

A modern streaming chat interface built with React, TypeScript, Vite, and Tailwind CSS.

## Features

- 💬 Real-time streaming chat interface
- 🌓 Dark mode support
- 📱 Responsive design
- ⚡ Fast development with Vite
- 🎨 Styled with Tailwind CSS
- 📝 TypeScript for type safety
- 🔄 Real-time message streaming
- 🌐 Configurable API endpoints via environment variables
- 📡 Axios for robust HTTP client with interceptors
- 🔄 Automatic request/response logging
- ⚠️ Enhanced error handling with custom messages

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env to set your API URL if different from default
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to:
```
http://localhost:3000
```

### Environment Variables

Create a `.env` file with the following variables:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── components/       # React components
│   ├── ChatInterface.tsx
│   ├── ChatSettings.tsx
│   ├── MessageList.tsx
│   ├── Message.tsx
│   └── MessageInput.tsx
├── config/          # Configuration
│   ├── api.ts       # API configuration
│   └── axios.ts     # Axios client setup & interceptors
├── services/        # API services
│   └── api.ts       # HTTP & streaming API client
├── types/          # TypeScript types
│   ├── api.ts      # API-related types
│   └── chat.ts     # Chat-related types
├── App.tsx         # Main app component
├── main.tsx        # Entry point
└── index.css       # Tailwind CSS imports
```

## API Integration

The UI uses **Axios** as the HTTP client for robust API communication with the following endpoints:

- **POST** `/api/v1/chat/stream` - Primary streaming endpoint (SSE)
- **POST** `/api/v1/chat/completions` - Non-streaming fallback
- **GET** `/api/v1/chat/history/{chatId}` - Chat history
- **GET** `/api/v1/models` - Available models

### Axios Features:
- 🔄 **Automatic retries** with exponential backoff
- 📝 **Request/response logging** for debugging
- ⚠️ **Enhanced error handling** with custom messages
- 🕒 **Configurable timeouts** (30s default)
- 🔍 **Request/response interceptors** for monitoring

Make sure the backend server is running and configured for CORS.

## Streaming Implementation

The chat uses Server-Sent Events (SSE) to stream messages in real-time:

1. User sends message
2. UI creates placeholder assistant message
3. Streams chunks from `/api/v1/chat/stream`
4. Updates UI with each chunk for real-time typing effect
5. Finalizes message when stream completes

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Chat Modes

- **Single**: One AI agent responds
- **Multiple**: Multiple AI agents can participate