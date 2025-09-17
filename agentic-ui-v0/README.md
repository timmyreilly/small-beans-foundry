# Agentic UI v0

A full-stack conversational AI application with Vue.js frontend and FastAPI backend powered by **Microsoft AutoGen** with Azure AI Foundry integration, featuring both single and multi-agent modes.

## Overview

Agentic UI v0 provides a comprehensive foundation for AutoGen integration with dual-mode operation: single agent for general conversations and multi-agent research teams for complex tasks.

## Architecture

- **Frontend**: Vue.js 3 with TypeScript, Pinia for state management, dynamic mode switching
- **Backend**: FastAPI with **single and multi-agent AutoGen systems**
- **AI Service**: Microsoft AutoGen with Azure AI Foundry project
- **Communication**: RESTful API with CORS configuration
- **Telemetry**: Comprehensive conversation tracking and monitoring

## Features

- 🤖 **Dual Agent Modes** - Single agent and multi-agent research teams
- 🔀 **Dynamic Mode Switching** - Toggle between modes with conversation clearing
- 🔍 **Multi-Agent Research** - ResearcherAgent + SummarizerAgent collaboration
- 🤝 **AutoGen Handoffs** - Intelligent agent-to-agent communication
- 💬 Clean chat interface with message history
- 🔐 Azure authentication with API key support
- 📊 Health monitoring and service status
- 📈 **Telemetry Integration** - Full conversation recording and analysis
- 🚀 Easy development startup with `start-dev.sh`
- 🧪 Comprehensive smoke tests for both agent modes

## Quick Start

### Prerequisites

- Node.js (v18+)
- Python (v3.10+) - AutoGen requirement
- Azure AI Foundry project with API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd agentic-ui-v0
   ```

2. **Configure Azure AI Foundry:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your Azure AI Foundry configuration
   cd ..
   ```

3. **Start development environment:**
   ```bash
   ./start-dev.sh
   ```

### Azure Configuration

Update `backend/.env` with your Azure AI Foundry details:

```env
# Your Azure AI Foundry project endpoint
AZURE_PROJECT_ENDPOINT=https://your-foundry-resource.services.ai.azure.com/api/projects/YourProjectName

# Your API key
AZURE_FOUNDRY_API_KEY=your-api-key-here

# Your model deployment name
MODEL_DEPLOYMENT_NAME=gpt-4o
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Project Structure

```
agentic-ui-v0/
├── backend/
│   ├── app/
│   │   ├── config/
│   │   │   ├── azure.py          # Azure configuration
│   │   │   └── telemetry.py      # OpenTelemetry configuration
│   │   ├── models/
│   │   │   └── models.py         # Pydantic models
│   │   ├── routers/
│   │   │   └── chat.py           # Chat API endpoints (single & multi-agent)
│   │   └── services/
│   │       ├── agent.py          # Single AutoGen agent
│   │       ├── multi_agent.py    # Multi-agent research system
│   │       └── session.py        # Session management
│   ├── main.py                   # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   └── .env.example             # Environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatInterface.vue # Chat UI with mode switching
│   │   ├── stores/
│   │   │   └── chat.ts          # Pinia chat store with agent modes
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript types
│   │   ├── App.vue              # Main Vue app
│   │   └── main.ts              # Vue app entry
│   ├── package.json             # Node dependencies
│   └── vite.config.ts           # Vite configuration
├── start-dev.sh                 # Development startup script
├── test_smoke.py                # Basic functional smoke test
├── test_multi_agent.py          # Extended multi-agent smoke test
└── README.md                    # This file
```

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send message to single AutoGen agent
- `POST /api/chat/multi-agent` - Send message to multi-agent research team
- `GET /api/agent-modes` - Get available agent modes for frontend

### Session Management
- `GET /api/sessions/{session_id}/messages` - Retrieve conversation history

### System Endpoints
- `GET /health` - Health check with Azure configuration status

## Agent Modes

### Single Agent Mode
- **Purpose**: General conversations and standard AI assistance
- **Agent**: Single AutoGen conversational agent
- **Use Cases**: Q&A, general assistance, casual conversations

### Multi-Agent Research Mode
- **Purpose**: Complex research tasks requiring web search and synthesis
- **Agents**: 
  - **ResearcherAgent**: Searches web for information (currently mocked)
  - **SummarizerAgent**: Analyzes and synthesizes research findings
- **Use Cases**: Research queries, trend analysis, comprehensive investigations
- **Flow**: User → ResearcherAgent → SummarizerAgent → User

## Development

### Manual Startup

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Vue.js):**
```bash
cd frontend
npm install
npm run dev
```

### Testing

**Run basic smoke test:**
```bash
# Make sure both frontend and backend are running
python test_smoke.py
```

**Run extended multi-agent tests:**
```bash
# Test both single and multi-agent functionality
python test_multi_agent.py
```

The smoke tests verify:
- ✅ Service health and Azure configuration
- ✅ Agent modes discovery endpoint
- ✅ Single agent chat functionality
- ✅ Multi-agent research functionality
- ✅ Session management and conversation history
- ✅ Multi-turn conversation flow in both modes
- ✅ Agent handoff patterns in multi-agent mode

## Configuration

### Backend Configuration
- Azure AI Foundry endpoint and API key
- Model deployment name
- Logging level and format
- CORS settings for frontend integration
- OpenTelemetry configuration for conversation tracking

### Frontend Configuration
- Vite development server with API proxy
- TypeScript strict mode
- Pinia state management with agent mode switching
- Axios for API communication

## Comparison with v1

### Enhanced Features:
- **Multi-Agent System**: Added ResearcherAgent + SummarizerAgent collaboration
- **Mode Switching**: Frontend toggle between single and multi-agent modes
- **Telemetry Integration**: Comprehensive conversation tracking and monitoring
- **AutoGen Handoffs**: Intelligent agent-to-agent communication patterns
- **Extended Testing**: Both basic and multi-agent smoke tests

### Maintained Features:
- ✅ Azure AI Foundry integration patterns
- ✅ Environment-based configuration
- ✅ Logging setup and health checks
- ✅ Session management
- ✅ Vue.js + TypeScript frontend
- ✅ Development tooling and scripts

## Troubleshooting

### Common Issues:

1. **Azure Configuration Errors**:
   ```bash
   # Check your .env file configuration
   cat backend/.env
   # Verify endpoint format and API key
   ```

2. **AutoGen Import Errors**:
   ```bash
   # Ensure Python 3.10+
   python --version
   # Reinstall AutoGen
   pip install -U "autogen-agentchat" "autogen-ext[azure]"
   ```

3. **Service Health Issues**:
   ```bash
   # Check health endpoint
   curl http://localhost:8000/health
   # Check logs in terminal where backend is running
   ```

4. **Smoke Test Failures**:
   ```bash
   # Ensure both services are running
   # Check Azure configuration in backend/.env
   # Verify API key has proper permissions
   ```

## Next Steps

### Immediate Enhancements:
- [ ] Replace mock web search with real search APIs (Bing, Google, etc.)
- [ ] Add more specialized agents (AnalystAgent, WriterAgent, etc.)
- [ ] Implement dynamic agent selection based on query type
- [ ] Add agent performance metrics and analytics

### Advanced Features:
- [ ] Create management of agent workflows
- [ ] Connecting to other existing agents and services
- [ ] Add conversation export functionality
- [ ] Implement conversation search and filtering
- [ ] Add support for file uploads and document analysis
- [ ] Configure custom system messages per agent
- [ ] Add authentication and user management
- [ ] Implement conversation sharing
- [ ] Add deployment configurations

### Multi-Agent Improvements:
- [ ] Add more research sources and tools
- [ ] Implement parallel agent execution
- [ ] Add agent consensus and voting mechanisms
- [ ] Create agent specialization based on domains
- [ ] Add real-time collaboration features

## Learn More

- [Microsoft AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Azure AI Foundry](https://azure.microsoft.com/en-us/products/ai-foundry/)
- [Vue.js 3 Documentation](https://vuejs.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)