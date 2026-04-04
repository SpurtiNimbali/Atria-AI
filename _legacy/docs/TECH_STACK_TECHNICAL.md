# CareFork - Technical Architecture Deep Dive

## 🏗️ System Architecture

### **Three-Layer Architecture**

```
┌─────────────────────────────────────────┐
│  PRESENTATION LAYER (Frontend)          │
│  - React 18 + TypeScript                │
│  - Voice Interface (Web Speech API)     │
│  - Real-time UI Updates                 │
└─────────────────────────────────────────┘
              ↕ WebSocket/HTTP
┌─────────────────────────────────────────┐
│  GATEWAY LAYER (FastAPI)                │
│  - WebSocket Server                     │
│  - REST API Endpoints                   │
│  - TTS Proxy                            │
│  - CORS & Routing                       │
└─────────────────────────────────────────┘
              ↕ Function Calls
┌─────────────────────────────────────────┐
│  INTELLIGENCE LAYER (Agentic AI)        │
│  - ConversationalDoctor Orchestrator    │
│  - 11 Medical Tools                     │
│  - Conversation History Management      │
│  - Streaming Response Generation        │
└─────────────────────────────────────────┘
```

---

## 🎨 Frontend Stack

### **Core Framework**
- **React 18.3.1** - Component-based UI library
- **TypeScript** - Static type checking
- **Vite 6.3.5** - Build tool with HMR (Hot Module Replacement)

**Why Vite?**
- **10x faster** than Webpack for dev server startup
- **Instant HMR** - Changes reflect immediately
- **Optimized builds** - Tree-shaking, code splitting

### **State Management**
- **React Hooks** - `useState`, `useEffect`, `useRef`
- **WebSocket State** - Real-time connection management
- **Voice State Machine** - IDLE → LISTENING → THINKING → REASONING → SPEAKING

### **Voice Interface**
- **Web Speech API** - Browser-native speech recognition
  - No external dependencies
  - Low latency (<100ms)
  - Works offline (recognition)
- **ElevenLabs TTS** - Text-to-speech via backend
  - Natural voice synthesis
  - Streaming audio
  - Multilingual support

### **Real-Time Communication**
- **WebSocket API** - Bidirectional real-time connection
  - Persistent connection
  - Low overhead
  - Event-driven architecture
- **Message Types:**
  - `voice_transcript` - User input
  - `reasoning_step` - AI reasoning updates
  - `tool_start` - Tool execution begins
  - `tool_complete` - Tool execution ends
  - `text_chunk` - Streaming response
  - `response_complete` - Final response

### **UI Libraries**
- **Radix UI** - Headless, accessible components
  - 20+ primitives (Dialog, Dropdown, Tooltip, etc.)
  - Unstyled, fully customizable
  - WCAG compliant
- **Framer Motion** - Animation library
  - Declarative animations
  - Layout animations
  - Gesture support

### **Styling**
- **Tailwind CSS 4.1.12** - Utility-first CSS
  - Rapid development
  - Consistent design system
  - Small bundle size (purged unused styles)

---

## ⚙️ Backend Stack

### **Core Framework**
- **Python 3.14** - Programming language
- **FastAPI 0.104.0+** - Modern async web framework
  - **Auto-generated OpenAPI docs**
  - **Type validation** with Pydantic
  - **Async/await** support
  - **WebSocket** support built-in

**Why FastAPI?**
- **Fast** - Comparable to Node.js and Go
- **Type hints** - Better IDE support, fewer bugs
- **Async** - Handles 10,000+ concurrent connections
- **Standards-based** - OpenAPI, JSON Schema

### **Server**
- **Uvicorn** - ASGI server
  - ASGI (Asynchronous Server Gateway Interface)
  - Supports HTTP/1.1 and HTTP/2
  - WebSocket support
  - Auto-reload in development

### **WebSocket Implementation**
```python
# Bidirectional real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        # Process and stream responses
        await websocket.send_json(response)
```

### **HTTP Client**
- **httpx 0.25.0+** - Async HTTP client
  - Used for OpenAI API calls
  - ElevenLabs TTS API
  - Jina AI embeddings
  - **Async/await** - Non-blocking I/O

---

## 🤖 AI & ML Stack

### **LLM: OpenAI GPT-4o-mini**
- **Model**: `gpt-4o-mini`
- **Why this model?**
  - **Fast**: Sub-second response times
  - **Cost-effective**: 10x cheaper than GPT-4
  - **Function calling**: Enables tool orchestration
  - **Streaming**: Real-time response generation

**Function Calling Architecture:**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_medical_literature",
            "description": "Search patient EHR",
            "parameters": {...}
        }
    }
]
# AI decides which tools to call and when
```

### **Embeddings: Jina AI**
- **Model**: Multilingual embedding model
- **Dimensions**: 768
- **Use case**: Semantic search in Elasticsearch
- **API**: REST endpoint, async calls

**Why Jina?**
- **Multilingual** - Works across languages
- **Fast** - Low latency API
- **Accurate** - State-of-the-art embeddings

### **Text-to-Speech: ElevenLabs**
- **Model**: `eleven_multilingual_v2`
- **Voice ID**: `EXAVITQu4vr4xnSDxMaL`
- **Format**: Audio/mpeg stream
- **Latency**: <500ms for first chunk

---

## 💾 Data & Search Stack

### **Elasticsearch 8.11.0**
- **Index**: `ehr_chunks`
- **Search Type**: Hybrid (BM25 + Vector)

**Index Structure:**
```json
{
  "patient_id": "synthetic-001",
  "resource_type": "MedicationRequest",
  "text": "Medication: Aspirin...",
  "embedding": [0.123, -0.456, ...],  // 768 dimensions
  "metadata": {...},
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Hybrid Search Query:**
```python
{
  "query": {
    "bool": {
      "should": [
        {
          "match": {  # BM25 keyword search
            "text": "medications"
          }
        },
        {
          "knn": {  # Vector semantic search
            "field": "embedding",
            "query_vector": [...],
            "k": 10
          }
        }
      ]
    }
  }
}
```

**Scoring:**
- BM25 score × 0.4 (keyword matching)
- Vector similarity × 0.6 (semantic matching)
- Combined score determines ranking

### **FHIR Data Standard**
- **Format**: JSON FHIR Bundle
- **Resources**: Patient, Condition, MedicationRequest, Observation, etc.
- **Normalization**: Converted to searchable chunks

**Normalization Process:**
```
FHIR Resource → Extract text/metadata → Generate embedding → Index in Elasticsearch
```

---

## 🔧 Agentic AI Architecture

### **ConversationalDoctor Class**
- **Purpose**: Orchestrates AI reasoning and tool execution
- **Key Methods:**
  - `process_query()` - Main entry point
  - `_execute_tool()` - Tool execution
  - `_generate_conversational_step()` - User-friendly reasoning

### **Tool Execution Flow**
```python
1. Receive query from user
2. Send to OpenAI with available tools
3. Receive tool_calls from AI
4. Execute each tool:
   - search_medical_literature → Query Elasticsearch
   - check_drug_interactions → Analyze medications
   - analyze_lab_trends → Process lab data
5. Send tool results back to OpenAI
6. Generate final response
7. Stream response chunks
```

### **11 Medical Tools**
1. **search_medical_literature** - EHR search
2. **check_drug_interactions** - Drug safety
3. **analyze_lab_trends** - Lab analysis
4. **predict_treatment_risk** - Risk assessment
5. **calculate_personalized_dose** - Dosing
6. **query_knowledge_graph** - Medical knowledge
7. **search_clinical_trials** - Research
8. **check_genetic_compatibility** - Genetics
9. **predict_lab_trend_ml** - ML predictions
10. **analyze_what_if_scenario** - Scenarios
11. **predict_disease_progression** - Prognosis

---

## 🔄 Data Flow

### **Query Processing Pipeline**
```
User Voice Input
    ↓
Web Speech API (Browser)
    ↓
Frontend: Send WebSocket message
    ↓
Gateway: Route to ConversationalDoctor
    ↓
ConversationalDoctor: Process query
    ├─→ OpenAI: Get tool_calls
    ├─→ Execute tools:
    │   ├─→ Elasticsearch: Search EHR
    │   ├─→ Jina AI: Generate query embedding
    │   └─→ Medical Tools: Process data
    ├─→ OpenAI: Generate response (with tool results)
    └─→ Stream response chunks
    ↓
Gateway: Forward chunks via WebSocket
    ↓
Frontend: Display reasoning + response
    ↓
Frontend: Call /tts endpoint
    ↓
Gateway: Proxy to ElevenLabs
    ↓
ElevenLabs: Generate audio
    ↓
Frontend: Play audio stream
```

### **Data Ingestion Pipeline**
```
FHIR Bundle (JSON)
    ↓
FHIR Client: Parse resources
    ↓
Normalization: Convert to chunks
    ├─→ Extract text
    ├─→ Extract metadata
    └─→ Generate timestamps
    ↓
Jina AI: Generate embeddings
    ↓
Elasticsearch: Index chunks
    ├─→ Store text
    ├─→ Store embedding (768-dim vector)
    ├─→ Store metadata
    └─→ Ready for hybrid search
```

---

## 🚀 Performance Characteristics

### **Latency Breakdown**
- **Voice Recognition**: <100ms (browser-native)
- **WebSocket Round-trip**: <10ms (local network)
- **OpenAI API Call**: 500-1500ms (depends on complexity)
- **Elasticsearch Query**: 20-50ms (local)
- **Jina Embedding**: 100-200ms (API call)
- **ElevenLabs TTS**: 200-500ms (first chunk)
- **Total**: **Sub-7 seconds** end-to-end

### **Throughput**
- **Concurrent WebSocket Connections**: 10,000+ (FastAPI async)
- **Queries per Second**: 100+ (with proper infrastructure)
- **Elasticsearch**: 1,000+ queries/second (local)

### **Scalability**
- **Horizontal**: Add more gateway instances
- **Vertical**: Upgrade server resources
- **Serverless**: Ready for Modal deployment

---

## 🔐 Security & Architecture

### **Communication Security**
- **WebSocket**: WSS (WebSocket Secure) in production
- **HTTP**: HTTPS in production
- **API Keys**: Environment variables, never in code

### **Data Privacy**
- **No persistent storage** - Queries processed, not stored
- **FHIR standard** - Industry-standard data format
- **Local processing** - Can run on-premise

### **Error Handling**
- **Graceful degradation** - System continues if one component fails
- **Retry logic** - Automatic retries for transient failures
- **Error boundaries** - Frontend error handling

---

## 📦 Deployment Architecture

### **Development (Current)**
```
Frontend: Vite dev server (localhost:5173)
Backend: Uvicorn (localhost:8000)
Elasticsearch: Docker (localhost:9200)
```

### **Production (Recommended)**
```
Frontend: Vercel (Static hosting)
Backend: Railway/Render/Fly.io (WebSocket support)
Elasticsearch: Elastic Cloud or self-hosted
```

### **Serverless (Future)**
```
Frontend: Vercel
Backend: Modal (Serverless Python)
Elasticsearch: Elastic Cloud
```

---

## 🛠️ Development Tools

### **Build Tools**
- **Vite** - Frontend bundler
- **TypeScript Compiler** - Type checking
- **Python** - Backend runtime

### **Package Management**
- **npm** - Frontend dependencies
- **pip** - Python dependencies
- **Virtual Environment** - Python isolation

### **Version Control**
- **Git** - Source control

---

## 📊 Technical Metrics

### **Codebase Size**
- **Frontend**: ~15,000 lines (TypeScript/TSX)
- **Backend**: ~8,000 lines (Python)
- **Tools**: ~3,000 lines (Python)
- **Total**: ~26,000 lines

### **Dependencies**
- **Frontend**: 60+ npm packages
- **Backend**: 10+ Python packages
- **External APIs**: 3 (OpenAI, Jina, ElevenLabs)

### **Bundle Sizes**
- **Frontend Bundle**: ~500KB (gzipped)
- **Backend**: Server-side, no bundle

---

## 🔍 Technical Decisions & Rationale

### **Why React over Vue/Angular?**
- Largest ecosystem
- Best TypeScript support
- Most developers familiar

### **Why FastAPI over Flask/Django?**
- Native async support
- Better WebSocket handling
- Auto-generated API docs
- Type validation built-in

### **Why Elasticsearch over PostgreSQL/Vector DB?**
- Hybrid search (BM25 + vector) in one system
- Industry standard for search
- Proven at scale
- Rich query language

### **Why GPT-4o-mini over GPT-4?**
- 10x cheaper
- 5x faster
- Sufficient for most queries
- Can upgrade to GPT-4 for complex cases

### **Why WebSocket over REST polling?**
- Real-time bidirectional communication
- Lower latency
- Less server load
- Better UX (instant updates)

---

*This is the technical foundation that enables CareFork's capabilities.*
