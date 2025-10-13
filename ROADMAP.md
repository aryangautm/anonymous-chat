# Backend Low-Level Design Document

## Table of Contents
1. [Project Overview & Architecture](#project-overview--architecture)
2. [Technology Stack](#technology-stack)
3. [System Components](#system-components)
4. [Database Design](#database-design)
5. [Authentication Flow](#authentication-flow)
6. [Knowledge Module System](#knowledge-module-system)
7. [RAG System Design](#rag-system-design)
8. [API Layer Design](#api-layer-design)
9. [Chat System Design](#chat-system-design)
10. [Security & Rate Limiting](#security--rate-limiting)
11. [Background Processing](#background-processing)
12. [Deployment Architecture](#deployment-architecture)

---

## Project Overview & Architecture

### High-Level System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  (Chat Interface + Owner Dashboard - Not in this document)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                         API Gateway                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   GraphQL    │  │     REST     │  │  Streaming   │          │
│  │  /graphql    │  │   /api/v1/   │  │  /chat/:id   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      Middleware Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Auth JWT    │  │ Rate Limit   │  │  CORS/Sec    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CRUD Ops    │  │  LangGraph   │  │  Knowledge   │          │
│  │              │  │  Chat Engine │  │  Retrieval   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                       Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │    Redis     │  │ Redis Pub/Sub│          │
│  │ +pgvector    │  │  Cache/RL    │  │  Task Queue  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                     External Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Firebase   │  │  Google AI   │  │   Sentence   │          │
│  │     Auth     │  │   (Gemini)   │  │ Transformers │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────┘
```

### Request Flow Patterns

**Authenticated Request (Owner Dashboard)**
```
Owner Browser 
  → GraphQL (/graphql) 
  → JWT Validation Middleware 
  → Parse Firebase Token 
  → CRUD Operation 
  → PostgreSQL 
  → Response
```

**Anonymous Chat Request**
```
Anonymous User 
  → POST /chat/{username} 
  → Rate Limiting (Redis) 
  → Session Validation 
  → LangGraph Processing:
    ├→ Vector Search (pgvector + Sentence Transformers)
    ├→ Conversation History
    ├→ LLM Generation (Google Gemini)
    └→ Store Message
  → Streaming Response (SSE)
```

**Background Processing**
```
Owner Uploads Document 
  → GraphQL Mutation 
  → Create Knowledge Module 
  → Publish to Redis Pub/Sub 
  → Worker Process:
    ├→ Parse Document
    ├→ Chunk Text
    ├→ Generate Embeddings (Sentence Transformers)
    └→ Store in pgvector
```

---

## Technology Stack

### Core Framework
- **FastAPI 0.118+**: Modern async web framework
- **Python 3.11+**: Async/await support, type hints
- **Uvicorn**: ASGI server with uvloop

### Database Layer
- **PostgreSQL 15+**: Primary relational database
- **pgvector Extension**: Vector similarity search for RAG
- **SQLAlchemy 2.0**: Async ORM
- **Alembic**: Database migrations
- **asyncpg**: Fast async PostgreSQL driver

### API Layer
- **Strawberry GraphQL**: GraphQL library with dataclasses
- **Pydantic v2**: Data validation
- **FastAPI StreamingResponse**: Server-Sent Events for chat

### AI & LLM Stack
- **LangGraph**: State machine for conversation flow
- **LangChain Core**: LLM abstractions
- **Google Generative AI (google-genai)**: Primary LLM (Gemini)
- **Sentence Transformers**: Local embedding model (all-mpnet-base-v2)
- **Semantic Router**: Content moderation and intent classification

### Caching & Queue
- **Redis 7+**: 
  - Rate limiting
  - Session storage
  - Caching
  - Pub/Sub for task distribution
- **Background workers**: Custom Python workers subscribing to Redis channels

### Authentication
- **Firebase Admin SDK**: JWT verification
- **python-jose**: JWT handling

### Development Tools
- **Black**: Code formatting
- **Isort**: Import sorting
- **Flake8**: Linting
- **Pytest**: Testing framework

---

## System Components

### Component Breakdown

#### 1. API Gateway Layer
- **GraphQL Endpoint** (`/graphql`)
  - All authenticated owner operations
  - Complex queries with multiple related resources
  - Mutations for persona and knowledge module management
  
- **REST Endpoints** (`/api/v1/`)
  - Authentication and registration
  - Public persona information (cacheable)
  - Simple health checks
  
- **Streaming Chat** (`/chat/{username}`)
  - SSE-based real-time chat
  - Session initialization
  - Message streaming

#### 2. Middleware Components
- **Authentication Middleware**
  - Firebase JWT verification
  - User lookup and validation
  - Request context injection
  
- **Rate Limiting Middleware**
  - IP-based rate limiting (60/min, 1000/hr)
  - Session-based rate limiting (10/min)
  - Redis-backed counters with TTL
  
- **Security Headers Middleware**
  - CORS configuration
  - Security headers (CSP, X-Frame-Options, etc.)
  - Request/Response logging

#### 3. Business Logic Services
- **Session Manager**
  - Anonymous session creation/validation
  - Redis-based session storage (1-hour TTL)
  - Session metadata tracking
  
- **Content Moderation Service**
  - Pre-emptive content checking
  - OpenAI moderation API fallback
  - Category-based rejection messages
  
- **Embeddings Service**
  - Sentence Transformers (all-mpnet-base-v2)
  - Local model inference (no API calls)
  - Batch embedding generation
  - Dimension: 768 (mpnet output)
  
- **Vector Search Service**
  - pgvector cosine similarity search
  - Persona-scoped retrieval
  - Priority-weighted results
  - Configurable similarity threshold
  
- **Context Builder**
  - RAG context assembly
  - Token budget management (2000 tokens max)
  - Source tracking and citation
  - History-aware context building
  
- **LLM Service**
  - Google Gemini integration via google-genai
  - Streaming response generation
  - Temperature and token limit control
  - Conversation history management
  
- **Rate Limiter**
  - Two-tier rate limiting (IP + Session)
  - Redis atomic operations
  - Sliding window implementation
  - Violation logging

#### 4. CRUD Operations
- **User CRUD**: User account management
- **Persona CRUD**: Persona creation, updates, deletion
- **Knowledge Module CRUD**: Module management with type validation
- **Knowledge Chunk CRUD**: Bulk chunk operations, embedding updates
- **Conversation CRUD**: Session and message storage
- **Feedback CRUD**: Owner feedback management

#### 5. Background Workers
- **Knowledge Processing Worker**
  - Subscribes to Redis channel: `knowledge_processing`
  - Document parsing (PDF, DOCX, TXT)
  - Web scraping for URL sources
  - Text chunking (500 tokens, 50 overlap)
  - Embedding generation (Sentence Transformers)
  - Bulk database insertion
  
- **Feedback Processing Worker**
  - Subscribes to Redis channel: `feedback_processing`
  - Converts feedback to high-priority Q&A modules
  - Automatic re-indexing
  
- **Analytics Worker**
  - Subscribes to Redis channel: `analytics`
  - Conversation statistics aggregation
  - Session cleanup (24h inactive)

---

## Database Design

### Schema Overview

#### Core Tables

**1. users**
- Purpose: Persona owner accounts
- Key Fields:
  - `id` (UUID, PK)
  - `firebase_uid` (VARCHAR, UNIQUE) - Links to Firebase
  - `email` (VARCHAR, UNIQUE)
  - `display_name` (VARCHAR, nullable)
  - `is_active` (BOOLEAN)
  - `created_at`, `updated_at` (TIMESTAMPTZ)
- Indexes: firebase_uid, email
- Relationships: One-to-Many with personas

**2. personas**
- Purpose: AI persona configurations
- Key Fields:
  - `id` (UUID, PK)
  - `user_id` (UUID, FK → users)
  - `username` (VARCHAR(50), UNIQUE) - For URL routing
  - `public_name` (VARCHAR(100))
  - `base_prompt`, `system_prompt` (TEXT, nullable)
  - `welcome_message` (TEXT, nullable)
  - `temperature` (FLOAT, default 0.7)
  - `max_tokens` (INTEGER, default 500)
  - `llm_provider` (VARCHAR(20), default 'google')
  - `llm_model` (VARCHAR(50), nullable)
  - `profile_image_url` (VARCHAR(512), nullable)
  - `social_links` (JSONB, nullable)
  - `custom_settings` (JSONB, nullable)
  - `is_active`, `is_public` (BOOLEAN)
  - `created_at`, `updated_at` (TIMESTAMPTZ)
- Indexes: user_id, username, is_active
- Relationships: 
  - Many-to-One with users
  - One-to-Many with knowledge_modules, conversations

**3. knowledge_modules**
- Purpose: Organize persona knowledge by type
- Key Fields:
  - `id` (UUID, PK)
  - `persona_id` (UUID, FK → personas)
  - `module_type` (VARCHAR(50)) - 'bio', 'qna', 'text_block', 'url_source', 'document', 'resume', 'services', 'social_media'
  - `title` (VARCHAR(255), nullable)
  - `content` (JSONB) - Type-specific structure
  - `priority` (INTEGER, default 1) - Higher = retrieved first
  - `is_active` (BOOLEAN)
  - `metadata` (JSONB, nullable)
  - `created_at`, `updated_at` (TIMESTAMPTZ)
- Indexes: persona_id, module_type, is_active
- Content Structure by Type:
  - bio: `{"text": "...", "traits": ["curious"]}`
  - qna: `{"pairs": [{"q": "...", "a": "..."}, ...]}`
  - text_block: `{"text": "..."}`
  - url_source: `{"url": "...", "scraped_content": "...", "last_scraped": "..."}`
  - document: `{"filename": "...", "file_path": "...", "extracted_text": "..."}`

**4. knowledge_chunks**
- Purpose: Vectorized text chunks for RAG
- Key Fields:
  - `id` (UUID, PK)
  - `module_id` (UUID, FK → knowledge_modules)
  - `chunk_text` (TEXT)
  - `chunk_index` (INTEGER) - Order within module
  - `embedding` (VECTOR(768)) - Sentence Transformers mpnet dimension
  - `token_count` (INTEGER, nullable)
  - `metadata` (JSONB, nullable)
  - `created_at` (TIMESTAMPTZ)
- Indexes:
  - module_id (B-tree)
  - embedding (IVFFlat with cosine ops, lists=100)
- Vector Index Configuration:
  - Algorithm: IVFFlat (Inverted File with Flat Compression)
  - Distance: Cosine similarity
  - Lists: 100 (for ~10K-100K vectors)

**5. conversations**
- Purpose: Anonymous chat sessions
- Key Fields:
  - `id` (UUID, PK) - Also serves as session_id
  - `persona_id` (UUID, FK → personas)
  - `visitor_metadata` (JSONB, nullable) - Browser, device (NO IP)
  - `started_at` (TIMESTAMPTZ)
  - `last_activity_at` (TIMESTAMPTZ)
  - `is_active` (BOOLEAN)
  - `message_count` (INTEGER, default 0)
  - `total_tokens_used` (INTEGER, default 0)
- Indexes: persona_id, started_at, is_active
- Privacy: IP addresses NEVER stored here (only in rate_limit_violations for admin use)

**6. messages**
- Purpose: Individual chat messages
- Key Fields:
  - `id` (UUID, PK)
  - `conversation_id` (UUID, FK → conversations)
  - `sender` (VARCHAR(10)) - 'VISITOR' or 'AI'
  - `content` (TEXT)
  - `sources_used` (JSONB, nullable) - For AI messages: `[{"chunk_id": "...", "relevance_score": 0.95}, ...]`
  - `tokens_used` (INTEGER, nullable)
  - `latency_ms` (INTEGER, nullable)
  - `metadata` (JSONB, nullable)
  - `created_at` (TIMESTAMPTZ)
- Indexes: conversation_id, created_at

**7. owner_feedback**
- Purpose: Owner corrections for persona improvement
- Key Fields:
  - `id` (UUID, PK)
  - `persona_id` (UUID, FK → personas)
  - `original_message_id` (UUID, FK → messages)
  - `visitor_question` (TEXT)
  - `original_response` (TEXT)
  - `improved_response` (TEXT)
  - `feedback_notes` (TEXT, nullable)
  - `is_applied` (BOOLEAN, default false)
  - `created_at` (TIMESTAMPTZ)
- Indexes: persona_id, is_applied
- Workflow: When applied, creates new high-priority Q&A module

**8. rate_limit_violations**
- Purpose: Monitoring and abuse detection
- Key Fields:
  - `id` (UUID, PK)
  - `ip_address` (INET) - Only table storing IPs
  - `endpoint` (VARCHAR(255))
  - `violation_type` (VARCHAR(50))
  - `violated_at` (TIMESTAMPTZ)
  - `request_count` (INTEGER)
  - `limit_threshold` (INTEGER)
- Indexes: ip_address, violated_at
- Access: Admin-only, not exposed to persona owners

### Database Extensions
- **uuid-ossp**: UUID generation
- **pgvector**: Vector similarity search

### Migration Strategy
- Alembic for versioned migrations
- `base_config.py`: Independent config for Alembic (database URL only)
- `config.py`: Full application config (inherits from BaseConfig for DB settings, adds all other env vars)

---

## Authentication Flow

### Firebase Integration

**Registration Flow**
1. User signs up via Firebase Auth on frontend
2. Frontend receives Firebase ID token
3. Frontend calls `POST /api/v1/auth/register` with token
4. Backend:
   - Verifies token with Firebase Admin SDK
   - Extracts uid and email from token claims
   - Checks if user exists (by firebase_uid)
   - If new: Creates user record in PostgreSQL
   - Returns user data
5. Frontend stores JWT for subsequent requests

**Authentication Flow**
1. User provides Firebase token in Authorization header: `Bearer <token>`
2. Auth middleware intercepts request
3. Verifies token with Firebase Admin SDK
4. Looks up user in database by firebase_uid
5. Checks user.is_active status
6. Injects user object into request context
7. Proceeds to endpoint handler

**Token Caching Strategy**
- Cache verified Firebase UIDs in Redis for 5 minutes
- Key: `auth:token:<hash(token)>` → firebase_uid
- Reduces Firebase API calls
- Still validates token signature, only caches lookup

### Authorization Levels
- **Public**: Chat endpoints, persona public info
- **Authenticated**: GraphQL queries/mutations
- **Owner-Only**: Persona management, conversation viewing (verified by user_id match)
- **Admin-Only**: Rate limit violation logs (not exposed via API)

---

## Knowledge Module System

### Module Types and Structure

#### 1. Bio Module
- **Purpose**: Core personality and background
- **Content Structure**:
  ```
  {
    "text": "Full bio text...",
    "traits": ["curious", "helpful", "technical"]
  }
  ```
- **Processing**: Single text block, chunked if > 500 tokens

#### 2. Q&A Module
- **Purpose**: Explicit question-answer pairs
- **Content Structure**:
  ```
  {
    "pairs": [
      {"q": "What do you do?", "a": "I'm a software engineer..."},
      {"q": "Where are you located?", "a": "San Francisco"}
    ]
  }
  ```
- **Processing**: Each pair becomes a chunk: "Q: ...\nA: ..."
- **Priority**: Highest for feedback-generated Q&As (priority=10)

#### 3. Text Block Module
- **Purpose**: General knowledge, articles, notes
- **Content Structure**:
  ```
  {
    "text": "Long form content..."
  }
  ```
- **Processing**: Chunked with overlap

#### 4. URL Source Module
- **Purpose**: Web content from external URLs
- **Content Structure**:
  ```
  {
    "url": "https://example.com/article",
    "scraped_content": "Extracted text...",
    "last_scraped": "2025-10-12T10:00:00Z"
  }
  ```
- **Processing**: Background scraping, cleaned HTML extraction

#### 5. Document Module
- **Purpose**: Uploaded files (PDF, DOCX, TXT)
- **Content Structure**:
  ```
  {
    "filename": "resume.pdf",
    "file_path": "/storage/...",
    "extracted_text": "Text from document..."
  }
  ```
- **Processing**: Format-specific parsers, page-aware chunking

### Text Processing Pipeline

**Chunking Strategy**
- **Chunk Size**: 500 tokens (using tiktoken for accurate counting)
- **Overlap**: 50 tokens between chunks
- **Rationale**: 
  - 500 tokens balances context vs. precision
  - Overlap prevents information loss at boundaries
  - Fits well within typical LLM context windows

**Tokenization**
- Use tiktoken with Gemini-compatible encoding
- Count tokens, not characters
- Critical for context budget management

**Document Parsing**
- **PDF**: pypdf library, page-by-page extraction
- **DOCX**: python-docx, paragraph-level extraction
- **TXT**: Direct UTF-8 decoding
- **Web**: BeautifulSoup, cleaned HTML (remove nav, footer, scripts)

---

## RAG System Design

### Embedding Generation

**Sentence Transformers Configuration**
- **Model**: all-mpnet-base-v2
- **Dimensions**: 768
- **Advantages over API-based**:
  - No API costs
  - No rate limits
  - Consistent local inference
  - Privacy (no data sent externally)
  - Faster for batch processing
- **Hardware**: Can run on CPU, GPU recommended for large batches
- **Batch Size**: Process up to 32 chunks per batch for efficiency

**Embedding Workflow**
1. Text chunking completed
2. Load Sentence Transformers model (cached in memory)
3. Batch encode all chunks
4. Normalize embeddings (built into mpnet)
5. Store as VECTOR(768) in PostgreSQL

### Vector Search Design

**Search Parameters**
- **top_k**: 5 results (configurable)
- **similarity_threshold**: 0.7 cosine similarity
- **Distance Metric**: Cosine distance (1 - cosine_similarity)
- **Index Type**: IVFFlat with 100 lists

**Search Query Flow**
1. Encode user query with Sentence Transformers
2. Execute pgvector similarity search:
   ```
   SELECT * FROM knowledge_chunks kc
   JOIN knowledge_modules km ON kc.module_id = km.id
   WHERE km.persona_id = ? 
     AND km.is_active = true
     AND 1 - (kc.embedding <=> query_embedding) >= threshold
   ORDER BY km.priority DESC, similarity_score DESC
   LIMIT top_k
   ```
3. Return chunks with metadata and scores

**Priority System**
- Module priority (1-10): Controls retrieval order
- High-priority modules (owner feedback) retrieved first
- Same-priority modules sorted by similarity score
- Enables semantic + rule-based hybrid retrieval

### Context Building

**Context Budget Management**
- **Max Context**: 2000 tokens
- **Allocation**:
  - System prompt: ~200 tokens
  - Retrieved context: ~1500 tokens
  - Conversation history: ~300 tokens (last 5 messages)
- **Overflow Handling**: Stop adding chunks when budget exceeded

**Context Assembly**
1. Search for relevant chunks
2. Sort by priority then similarity
3. Accumulate chunks until token budget reached
4. Format with source attribution: `[Source: qna - Resume]\n{text}`
5. Track which chunks used for citation

**Citation Tracking**
- Store chunk_id and similarity_score for each used chunk
- Save in message.sources_used as JSONB
- Enables "why did AI say this?" debugging for owners

---

## API Layer Design

### GraphQL API (Strawberry)

**Endpoint**: `/graphql`

**Authentication**: All operations require valid Firebase JWT

**Query Operations**
- `me`: Get current user info
- `persona(username)`: Get single persona (public or owned)
- `myPersonas`: List all personas owned by current user
- `knowledgeModules(personaId)`: List all modules for a persona (ownership verified)
- `conversations(personaId, page, pageSize)`: Paginated conversation list
- `conversationDetail(conversationId)`: Full conversation with messages
- `ownerFeedbackList(personaId, isApplied?)`: List feedback entries

**Mutation Operations**
- `createPersona(input)`: Create new persona
- `updatePersona(personaId, input)`: Update persona settings
- `deletePersona(personaId)`: Delete persona and all data
- `addKnowledgeModule(personaId, input)`: Add knowledge module (triggers background processing)
- `updateKnowledgeModule(moduleId, input)`: Update existing module
- `deleteKnowledgeModule(moduleId)`: Delete module and chunks
- `submitOwnerFeedback(personaId, input)`: Submit response correction

**GraphQL Schema Features**
- Custom scalars: UUID, DateTime, JSON
- Input validation via Pydantic models
- Ownership verification on all persona operations
- Async resolvers for database queries
- Dataloader pattern for N+1 query prevention (future optimization)

**Context Injection**
- Database session
- Current user (from auth middleware)
- Request object

### REST API Endpoints

**Authentication Endpoints** (`/api/v1/auth`)
- `POST /register`: User registration with Firebase token
- `GET /verify`: Token verification

**Public Endpoints** (`/api/v1/public`)
- `GET /persona/{username}`: Public persona info (unauthenticated)
  - Returns: username, public_name, welcome_message, profile_image_url, social_links
  - Cacheable (Redis, 5 min TTL)
- `GET /health`: Health check

**Chat Endpoints** (`/api/v1/chat`)
- `POST /{username}/init`: Initialize chat session
  - Returns: session_id, welcome_message
  - Creates conversation record, Redis session
- `POST /{username}/stream`: Streaming chat (SSE)
  - Input: message, session_id
  - Output: Server-Sent Events stream
  - Events: `{token}`, `{done, latency_ms}`, `{error}`

### Streaming Chat Protocol

**Server-Sent Events (SSE) Format**
```
data: {"token": "Hello"}\n\n
data: {"token": " there"}\n\n
data: {"done": true, "latency_ms": 1250}\n\n
```

**Why SSE over WebSockets**
- Simpler infrastructure (HTTP/2 compatible)
- One-way communication sufficient
- Automatic reconnection
- No connection pooling issues
- Works through most proxies
- Lower overhead than WebSocket handshake

**Streaming Implementation**
- FastAPI StreamingResponse with async generator
- Yield tokens as they're generated by Gemini
- Client parses SSE stream and renders incrementally
- Feels real-time despite being HTTP

---

## Chat System Design

### Session Management

**Session Lifecycle**
1. **Creation**: POST `/chat/{username}/init`
   - Generate UUID as session_id
   - Store in Redis: `session:{id}` → {persona_id, created_at, message_count}
   - Set TTL: 3600 seconds (1 hour)
   - Create conversation record in PostgreSQL
   - Return session_id to client

2. **Active Session**: During chat
   - Client includes session_id in each request
   - Backend validates session exists in Redis
   - Extends TTL on each activity
   - Increments message_count

3. **Expiration**: After 1 hour of inactivity
   - Redis automatically removes session
   - Conversation remains in PostgreSQL (for owner)
   - Visitor loses access (cannot resume)

**Session Storage**
- **Redis**: Fast validation, automatic expiry, metadata
- **PostgreSQL**: Permanent storage, full message history, analytics
- **Why Both**: Redis for speed, PostgreSQL for persistence

### Content Moderation

**Pre-emptive Checking**
- Check all visitor messages BEFORE LLM call
- Prevents wasted API costs on harmful content
- Uses OpenAI Moderation API (cheap/free)
- Alternative: Semantic router with local classification

**Moderation Categories**
- hate: Hate speech
- harassment: Harassing content
- self-harm: Self-harm content → provide mental health resources
- sexual: Sexually explicit content
- violence: Violent content

**Response Strategy**
- If flagged: Return category-specific rejection message
- No LLM call made
- Still log the attempt (for abuse monitoring)

**Performance**: Adds ~100-200ms latency, acceptable tradeoff

### LLM Integration (Google Gemini)

**Configuration**
- **Provider**: Google Generative AI (google-genai library)
- **Model**: gemini-1.5-flash or gemini-1.5-pro (persona-configurable)
- **Streaming**: Native streaming support
- **Parameters**:
  - temperature: 0.0-2.0 (persona-specific, default 0.7)
  - max_tokens: 50-2000 (persona-specific, default 500)

**Message Format for Gemini**
```
System: {system_prompt}
System: Knowledge Context:\n{retrieved_context}
User: {history_message_1}
Assistant: {history_message_1_response}
User: {current_query}
```

**Streaming Implementation**
- Use Gemini's streaming API
- Yield tokens as they arrive
- Accumulate full response for database storage
- Track token count and latency

**Error Handling**
- Retry on transient errors (2 attempts, exponential backoff)
- Generic error message to user
- Log full error for debugging
- Fallback: "I'm experiencing technical difficulties"

### Conversation Flow (LangGraph)

**State Machine Design**

**States**
1. **Moderate**: Content moderation check
2. **Retrieve**: RAG context retrieval
3. **Generate**: LLM response generation

**State Transitions**
```
START → Moderate
  ├─ if flagged → Generate (with rejection message)
  └─ if clean → Retrieve → Generate → END
```

**State Data**
- messages: Conversation history
- retrieved_context: RAG results
- sources_used: Citation tracking
- persona_id, system_prompt, temperature, max_tokens
- session_id
- current_response, tokens_generated
- content_flagged: Boolean flag

**LangGraph vs Direct Implementation**
- LangGraph used for non-streaming batch processing (future)
- Streaming chat bypasses LangGraph (direct service calls)
- Reason: LangGraph doesn't natively stream well
- Compromise: Use LangGraph for background analysis, direct calls for chat

---

## Security & Rate Limiting

### Rate Limiting Strategy

**Two-Tier System**
1. **IP-Based (Global)**
   - 60 requests/minute
   - 1000 requests/hour
   - Prevents mass spam from single source
   - Redis keys: `ratelimit:ip:{ip}:{endpoint}:minute|hour`

2. **Session-Based (Per Conversation)**
   - 10 messages/minute
   - Prevents individual conversation abuse
   - Redis keys: `ratelimit:session:{id}:minute`

**Implementation**
- Redis INCR command (atomic)
- EXPIRE for automatic cleanup
- Return 429 status with Retry-After header
- Log violations to PostgreSQL (with IP address)

**Bypass Rules**
- Health checks: No rate limiting
- Static assets: No rate limiting
- GraphQL introspection: Subject to IP limits only

### Security Headers

**Headers Applied**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy`: (to be configured based on frontend needs)

**CORS Configuration**
- Allowed origins from environment variable (whitelist)
- Credentials: Allowed (for cookies if needed)
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: All (including Authorization)

### Privacy Considerations

**IP Address Handling**
- **NEVER** stored in conversations or messages
- Only stored in rate_limit_violations (admin access only)
- Persona owners NEVER see visitor IPs
- Platform admin can investigate abuse

**Visitor Anonymity**
- Session ID is the only identifier exposed to owner
- No tracking across sessions
- No cookies or persistent identifiers
- Browser/device info stored non-identifying (browser type, not fingerprint)

### SQL Injection Prevention
- SQLAlchemy ORM for all queries
- Parameterized queries for raw SQL (vector search)
- No string concatenation with user input
- Input validation via Pydantic

### XSS Prevention
- FastAPI auto-escapes JSON responses
- Frontend responsible for HTML escaping
- Security headers prevent inline scripts

---

## Background Processing

### Redis Pub/Sub Architecture

**Why Redis Pub/Sub over RabbitMQ**
- Simpler setup (one less service)
- Already using Redis for caching/rate limiting
- Sufficient for MVP scale
- Fire-and-forget messaging pattern
- Can migrate to RabbitMQ/Kafka for more complex workflows later

**Channel Design**
- `knowledge_processing`: Document/URL processing tasks
- `feedback_processing`: Owner feedback application
- `analytics`: Statistics and cleanup tasks

**Message Format**
```json
{
  "task_type": "process_knowledge_module",
  "data": {
    "module_id": "uuid",
    "priority": "normal"
  },
  "timestamp": "ISO-8601"
}
```

### Worker Architecture

**Worker Process Design**
- Separate Python process(es) from main API server
- Subscribe to Redis channels on startup
- Process messages asynchronously
- Database connection pooling (separate from API)
- Graceful shutdown on SIGTERM

**Worker Types**
1. **Knowledge Worker**: Handles knowledge processing
2. **Feedback Worker**: Handles feedback application
3. **Analytics Worker**: Handles stats and cleanup

**Scaling**
- Can run multiple instances of each worker type
- Redis Pub/Sub broadcasts to all subscribers (idempotency needed)
- Alternative: Use Redis Streams for exactly-once processing

### Knowledge Processing Workflow

**Trigger**: GraphQL mutation `addKnowledgeModule` or `updateKnowledgeModule`

**Flow**
1. API creates/updates knowledge_modules record
2. Publishes message to `knowledge_processing` channel
3. Worker receives message
4. Loads module from database
5. Based on module_type:
   - **Bio/Text**: Direct text chunking
   - **Q&A**: Format as "Q: ...\nA: ..." per pair
   - **URL**: Scrape with httpx + BeautifulSoup, clean HTML
   - **Document**: Parse with pypdf/python-docx, extract text
6. Chunk text (500 tokens, 50 overlap)
7. Generate embeddings with Sentence Transformers (batch)
8. Store chunks with embeddings in knowledge_chunks
9. Update module status/timestamp

**Error Handling**
- Log errors to database or logging system
- Retry logic: 2 attempts with exponential backoff
- If fails: Mark module with error status
- Owner notified via GraphQL query (status field)

### Feedback Processing Workflow

**Trigger**: GraphQL mutation `submitOwnerFeedback`

**Flow**
1. API creates owner_feedback record
2. Publishes message to `feedback_processing` channel
3. Worker receives message
4. Loads feedback record
5. Creates new knowledge_module (type='qna', priority=10)
6. Content: `{"pairs": [{"q": visitor_question, "a": improved_response}]}`
7. Marks feedback.is_applied = true
8. Triggers knowledge processing for new module

**Result**: Future similar questions retrieve corrected answer first

### Analytics Workflow

**Scheduled Tasks** (via cron or periodic Redis publish)
1. **Session Cleanup** (every hour)
   - Find conversations with last_activity > 24h ago
   - Mark is_active = false
   - Frees up database from inactive sessions

2. **Statistics Aggregation** (daily)
   - Per-persona metrics: total conversations, messages, tokens
   - Popular question topics (simple keyword extraction)
   - Store in separate analytics tables

3. **Vector Index Optimization** (weekly)
   - VACUUM ANALYZE on knowledge_chunks
   - Rebuild IVFFlat index if needed

---

## Deployment Architecture

### Environment Setup

**Environment Variables**
- **Database**: DATABASE_URL, SYNC_DATABASE_URL
- **Redis**: REDIS_URL, REDIS_RATE_LIMIT_DB
- **Firebase**: FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID
- **Google AI**: GOOGLE_AI_API_KEY, GOOGLE_AI_MODEL
- **App**: APP_ENV, APP_AUTH_KEY, CORS_ORIGINS, API_V1_PREFIX
- **Rate Limiting**: RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR, SESSION_RATE_LIMIT_PER_MINUTE
- **Moderation**: ENABLE_CONTENT_MODERATION, MODERATION_THRESHOLD

**Configuration Pattern**
- `base_config.py`: Minimal config for Alembic (DATABASE_URL only)
- `config.py`: Full application config (inherits base, adds all other settings)
- Separation allows Alembic to run without needing all env vars

### Docker Deployment

**Services**
1. **PostgreSQL + pgvector**: Database service
2. **Redis**: Cache, rate limiting, pub/sub
3. **API Server**: FastAPI application (uvicorn)
4. **Background Workers**: Python workers subscribing to Redis

**Docker Compose Structure**
- Separate containers for each service
- Volume mounts for persistence (PostgreSQL data, uploaded files)
- Health checks for dependency ordering
- Network isolation

**Scaling Considerations**
- API server: Scale horizontally behind load balancer
- Workers: Scale by worker type based on queue depth
- Redis: Single instance for MVP, Redis Cluster for production
- PostgreSQL: Single instance initially, read replicas for analytics later

### Production Checklist

**Infrastructure**
- [ ] Set up production PostgreSQL with pgvector extension
- [ ] Configure Redis (persistence enabled, maxmemory policy)
- [ ] Set up load balancer (Nginx/Traefik) with SSL
- [ ] Configure DNS and domains

**Security**
- [ ] Set up Firebase project and download credentials
- [ ] Secure all environment variables (use secrets manager)
- [ ] Configure CORS for production domains only
- [ ] Set up rate limiting thresholds
- [ ] Enable security headers
- [ ] Configure firewall rules

**Monitoring**
- [ ] Set up application logging (structured JSON logs)
- [ ] Configure error tracking (Sentry or similar)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Database performance monitoring
- [ ] Redis monitoring (memory, hit rate)
- [ ] Set up alerts (error rate, latency, downtime)

**Backup & Recovery**
- [ ] PostgreSQL automated backups (daily, 30-day retention)
- [ ] Test backup restoration procedure
- [ ] Redis persistence (RDB + AOF)
- [ ] Document recovery procedures

**Performance**
- [ ] Database connection pooling (async: 5-20, sync: 2-10)
- [ ] Redis connection pooling
- [ ] Query optimization (EXPLAIN ANALYZE on slow queries)
- [ ] Cache public persona info (5 min TTL)
- [ ] CDN for static assets

**CI/CD**
- [ ] Automated testing on PR
- [ ] Automated migrations on deployment
- [ ] Blue-green deployment strategy
- [ ] Rollback procedure documented

### Monitoring Metrics

**Application Metrics**
- Requests per second (by endpoint)
- Response latency (P50, P95, P99)
- Error rate (5xx responses)
- Rate limit hits
- Active chat sessions
- Background task processing time
- Queue depth (Redis list length)

**Business Metrics**
- New user registrations
- Active personas
- Total conversations
- Messages per conversation
- Token usage (cost tracking)
- Embedding generation throughput

**Infrastructure Metrics**
- Database connection pool utilization
- Redis memory usage
- CPU/RAM usage per service
- Disk space
- Network I/O

---

## Implementation Timeline

### Week 1-2: Foundation
- Project structure setup
- PostgreSQL + pgvector installation
- Database schema implementation via Alembic
- Firebase authentication integration
- Basic FastAPI app with health check

### Week 3-4: Core Features
- All SQLAlchemy models and Pydantic schemas
- CRUD operations for all entities
- Sentence Transformers integration
- Text processing utilities (chunking, parsing)
- RAG system (embedding generation, vector search)
- Context builder

### Week 5-6: API Layer
- Strawberry GraphQL setup
- All GraphQL queries and mutations
- REST authentication endpoints
- Public persona endpoint
- Streaming chat endpoint with SSE
- LLM service (Gemini integration)

### Week 7-8: Security & Workers
- Rate limiting middleware (Redis)
- Content moderation service
- Security headers middleware
- Redis Pub/Sub setup
- Background workers (knowledge, feedback, analytics)
- Session management

### Week 9-10: Testing & Deployment
- Unit tests for services
- Integration tests for API endpoints
- Docker Compose configuration
- Production environment setup
- Monitoring and logging
- Performance optimization
- Documentation

---

## Key Design Decisions Summary

### Technology Choices
1. **Google Gemini over OpenAI**: Cost-effective, good performance, streaming support
2. **Sentence Transformers over API embeddings**: No cost, no rate limits, privacy
3. **Redis Pub/Sub over RabbitMQ**: Simplicity, already using Redis
4. **SSE over WebSockets**: Simpler infrastructure, sufficient for use case
5. **GraphQL + REST hybrid**: GraphQL for complex queries, REST for simple/cacheable ops
6. **IVFFlat over HNSW**: More mature, simpler configuration, sufficient for MVP scale

### Architecture Decisions
1. **Hybrid session storage**: Redis for speed, PostgreSQL for persistence
2. **Pre-emptive moderation**: Cost savings, prevents LLM abuse
3. **Priority-weighted retrieval**: Combines semantic search with rules
4. **Owner feedback loop**: Self-improving personas without fine-tuning
5. **Two-tier rate limiting**: Prevents both mass abuse and individual spam
6. **IP privacy**: Owners never see visitor IPs, only admin for abuse cases

### Scalability Path
1. **Initial**: Single server, single PostgreSQL, single Redis
2. **Scale Phase 1**: Horizontal API scaling, worker scaling by type
3. **Scale Phase 2**: PostgreSQL read replicas, Redis Cluster
4. **Scale Phase 3**: Microservices split (chat, knowledge, analytics)
5. **Scale Phase 4**: Dedicated vector database (Qdrant, Weaviate)

---

## End of Design Document

This document provides the complete low-level design for the anonymous AI persona chat backend system. All architectural decisions are documented with rationale, and the system is designed to be scalable from MVP to production.
