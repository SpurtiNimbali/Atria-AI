# CareFork - Tech Stack Documentation

## Overview
CareFork is a conversational caregiver copilot that "forks" post-care trajectories in real-time, grounded in discharge documents and evidence. The system uses an agentic AI approach with transparent reasoning and document-grounded responses.

---

## 🎨 Frontend

### Core Framework
- **React 18.3.1** - UI library
- **TypeScript** - Type safety
- **Vite 6.3.5** - Build tool and dev server
- **React Router 7.13.0** - Client-side routing

### UI Libraries & Components
- **Radix UI** - Headless UI primitives
  - Accordion, Alert Dialog, Avatar, Checkbox, Collapsible
  - Context Menu, Dialog, Dropdown Menu, Hover Card
  - Label, Menubar, Navigation Menu, Popover
  - Progress, Radio Group, Scroll Area, Select
  - Separator, Slider, Switch, Tabs, Toggle, Tooltip
- **Material-UI (MUI) 7.3.5** - Component library
  - @mui/material, @mui/icons-material
- **Emotion** - CSS-in-JS styling
  - @emotion/react 11.14.0
  - @emotion/styled 11.14.1

### Styling
- **Tailwind CSS 4.1.12** - Utility-first CSS framework
- **@tailwindcss/vite** - Vite plugin for Tailwind
- **PostCSS** - CSS processing
- **Custom fonts**: Crimson Pro (serif), Space Mono (monospace)

### Animation & Motion
- **Motion (Framer Motion) 12.23.24** - Animation library
  - Used for smooth transitions, entrance animations
  - Agentic reasoning step animations
  - Voice interface state transitions

### Forms & Validation
- **React Hook Form 7.55.0** - Form state management
- **Input OTP 1.4.2** - OTP input components

### Data Visualization
- **Recharts 2.15.2** - Chart library
- **React Responsive Masonry 2.7.1** - Responsive grid layouts

### Utilities
- **clsx** - Conditional class names
- **tailwind-merge** - Merge Tailwind classes
- **class-variance-authority** - Component variants
- **date-fns 3.6.0** - Date utilities
- **cmdk 1.1.1** - Command menu component

### Voice & Audio
- **Web Speech API** - Browser-native speech recognition
- **Web Audio API** - Audio playback
- **ElevenLabs TTS** - Text-to-speech (via backend)

### Other Libraries
- **Lucide React 0.487.0** - Icon library
- **Sonner 2.0.3** - Toast notifications
- **Vaul 1.1.2** - Drawer component
- **React Day Picker 8.10.1** - Date picker
- **React DnD** - Drag and drop
- **Embla Carousel React 8.6.0** - Carousel component

---

## 🔧 Backend

### Core Framework
- **Python 3.14** - Programming language
- **FastAPI 0.104.0+** - Modern async web framework
- **Uvicorn** - ASGI server (with standard extras)
- **Pydantic 2.5.0+** - Data validation

### WebSocket & Real-time
- **WebSockets 12.0+** - Real-time bidirectional communication
- **FastAPI WebSocket** - WebSocket support

### HTTP Client
- **httpx 0.25.0+** - Async HTTP client
  - Used for OpenAI API calls
  - ElevenLabs TTS API calls
  - Jina AI embeddings API

### Environment & Configuration
- **python-dotenv 1.0.0+** - Environment variable management

### Serverless (Optional)
- **Modal 0.63.0+** - Serverless Python platform
  - Ready for production deployment
  - Currently using local deployment

---

## 🤖 AI & ML

### LLM
- **OpenAI API 1.6.0+**
  - **GPT-4o-mini** - Primary model (fast, cost-effective)
  - **GPT-4** - Available for complex reasoning
  - Function calling for tool orchestration
  - Streaming responses

### Embeddings
- **Jina AI API** - Vector embeddings
  - 768-dimensional vectors
  - Multilingual support
  - Used for semantic search in Elasticsearch

### Text-to-Speech
- **ElevenLabs API**
  - Model: `eleven_multilingual_v2`
  - Voice ID: `EXAVITQu4vr4xnSDxMaL`
  - Returns audio/mpeg stream

---

## 💾 Data & Search

### Search Engine
- **Elasticsearch 8.11.0** (8.x, <9.0.0)
  - Hybrid search (BM25 + vector embeddings)
  - Index: `ehr_chunks`
  - Local Docker deployment (dev)
  - Elastic Cloud ready (production)

### Data Standards
- **FHIR (Fast Healthcare Interoperability Resources)**
  - Patient, Condition, MedicationRequest
  - Observation, Encounter, Procedure
  - Coverage (Insurance), AllergyIntolerance
  - Synthetic patient data for development

### Data Processing
- **Custom EHR Parser** (`modal/ehr_parser.py`)
  - Extracts structured data from FHIR bundles
  - Normalizes to searchable chunks
  - Dashboard data extraction

---

## 🏗️ Architecture Components

### Gateway (`gateway/main.py`)
- FastAPI WebSocket server
- Routes requests to agent
- Handles TTS endpoint
- CORS middleware
- Environment variable loading

### Conversational Doctor (`modal/conversational_doctor.py`)
- Agentic AI orchestrator
- Tool execution
- Conversation history management
- Streaming responses
- Reasoning step generation

### Medical Tools (`modal/tools/`)
- `search_medical_literature` - EHR search
- `check_drug_interactions` - Drug safety
- `analyze_lab_trends` - Lab analysis
- `predict_treatment_risk` - Risk assessment
- `calculate_personalized_dose` - Dosing
- `query_knowledge_graph` - Medical knowledge
- `search_clinical_trials` - Research
- `check_genetic_compatibility` - Genetics
- `predict_lab_trend_ml` - ML predictions
- `analyze_what_if_scenario` - Scenario analysis
- `predict_disease_progression` - Prognosis

### Elasticsearch Client (`modal/elastic_client.py`)
- Connection management
- Index operations
- Hybrid search queries
- Document retrieval

### FHIR Client (`modal/fhir_client.py`)
- FHIR server integration
- Resource fetching
- Patient data aggregation

---

## 🔐 Environment Variables

### Frontend
```bash
VITE_BACKEND_URL=http://localhost:8000  # Backend API URL
```

### Backend
```bash
OPENAI_API_KEY=sk-...                    # OpenAI API key
JINA_API_KEY=jina_...                    # Jina AI embeddings key
ELASTIC_URL=http://localhost:9200         # Elasticsearch URL
ELEVENLABS_API_KEY=sk_...                # ElevenLabs TTS key
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL # Voice ID
ELEVENLABS_MODEL_ID=eleven_multilingual_v2 # Model ID
ALLOWED_ORIGINS=http://localhost:5173,... # CORS origins
```

---

## 📦 Package Management

### Frontend
- **npm** - Node package manager
- **package.json** - Dependencies defined
- **package-lock.json** - Lock file

### Backend
- **pip** - Python package manager
- **requirements.txt** - Python dependencies
- **Virtual environment** - Isolated Python environment

---

## 🚀 Deployment

### Frontend
- **Vercel** - Recommended
  - Vite build
  - Static site hosting
  - Environment variables support
  - See `figma_prototype/DEPLOYMENT.md`

### Backend
- **Railway** - Recommended (WebSocket support)
- **Render** - Alternative
- **Fly.io** - Alternative
- **Modal** - Serverless option (future)

### Database/Search
- **Elasticsearch**
  - Local Docker (development)
  - Elastic Cloud (production)
  - Self-hosted (production)

---

## 🛠️ Development Tools

### Build Tools
- **Vite** - Fast build tool
- **TypeScript** - Type checking
- **ESLint** - Code linting (if configured)

### Version Control
- **Git** - Version control

### Containerization
- **Docker** - Container runtime
- **docker-compose.yml** - Elasticsearch setup

---

## 📊 Data Flow

```
User Voice Input
    ↓
Web Speech API (Browser)
    ↓
Frontend (React/Vite)
    ↓
WebSocket → Gateway (FastAPI)
    ↓
Conversational Doctor (Python)
    ↓
    ├─→ OpenAI GPT-4o-mini (Reasoning)
    ├─→ Elasticsearch (EHR Search)
    ├─→ Jina AI (Embeddings)
    └─→ Medical Tools (Various)
    ↓
Response Generation
    ↓
ElevenLabs TTS
    ↓
Audio Stream → Frontend
    ↓
Audio Playback
```

---

## 🔄 Real-time Communication

- **WebSocket** - Bidirectional real-time communication
  - Client: Browser WebSocket API
  - Server: FastAPI WebSocket endpoint
  - Message types:
    - `voice_transcript` - User voice input
    - `reasoning_step` - AI reasoning updates
    - `tool_start` - Tool execution start
    - `tool_complete` - Tool execution complete
    - `text_chunk` - Streaming response chunks
    - `response_complete` - Final response
    - `timeline_commit` - Timeline updates

---

## 🎯 Key Features Enabled by Tech Stack

1. **Voice-First Interface** - Web Speech API + ElevenLabs TTS
2. **Real-time Updates** - WebSocket bidirectional communication
3. **Document-Grounded** - Elasticsearch hybrid search
4. **Transparent Reasoning** - Streaming reasoning steps
5. **Fast Development** - Vite hot reload + FastAPI auto-reload
6. **Type Safety** - TypeScript + Pydantic
7. **Modern UI** - React + Tailwind + Framer Motion
8. **Scalable** - Modal-ready for serverless deployment

---

## 📝 Notes

- **No medical advice** - Educational and planning support only
- **All recommendations grounded** - Must cite source documents
- **Probabilities from rules** - Not LLM speculation
- **Complete audit trail** - Full reasoning trace

---

## 🔗 External Services

1. **OpenAI** - LLM API
2. **Jina AI** - Embeddings API
3. **ElevenLabs** - Text-to-Speech API
4. **Elasticsearch** - Search engine (local or cloud)

---

*Last Updated: 2025-02-15*
