# Implementation Tasks

## Task Breakdown

### 1. Chainlit Application Module (src/chainlit/)

#### 1.1 Core Module Setup
- [ ] Create `src/chainlit/` directory structure
- [ ] Create `src/chainlit/__init__.py` with exports
- [ ] Create `src/chainlit/constants.py` with timeout/retry values
- [ ] Create `src/chainlit/config.py` with ChainlitSettings class

#### 1.2 SSE Client Implementation
- [ ] Create `src/chainlit/sse_client.py`
- [ ] Implement SSE stream parsing (event/data lines)
- [ ] Implement auto-retry with exponential backoff using tenacity
- [ ] Implement error categorization (retryable vs non-retryable)

#### 1.3 Event Handlers
- [ ] Create `src/chainlit/handlers.py`
- [ ] Implement `@cl.on_chat_start` with welcome message + suggested prompts
- [ ] Implement `@cl.on_message` with SSE stream handling
- [ ] Implement tool step visualization (name only)
- [ ] Implement inline error display with human-readable messages

#### 1.4 Main Application
- [ ] Create `src/chainlit/app.py`
- [ ] Wire up handlers
- [ ] Configure cl.user_session for settings storage

### 2. Chainlit Configuration (.chainlit/)

#### 2.1 UI Configuration
- [ ] Create `.chainlit/config.toml` with UI settings
- [ ] Configure app name: "VeraMoney Assistant"
- [ ] Configure theme and layout
- [ ] Disable file upload (not needed for proxy)

#### 2.2 Settings
- [ ] Create `.chainlit/settings.json` if needed

### 3. Docker Configuration

#### 3.1 docker-compose.yml
- [ ] Add `chainlit` service definition
- [ ] Configure environment variables (BACKEND_URL, CHAINLIT_API_KEY)
- [ ] Set port mapping (${CHAINLIT_PORT:-8002}:8000)
- [ ] Add dependency on `app` service
- [ ] Configure network (vera-network)
- [ ] Set command: `chainlit run src/chainlit/app.py --host 0.0.0.0 --port 8000`

#### 3.2 Dockerfile (Optional)
- [ ] Consider adding chainlit to development stage if needed

### 4. Environment Configuration

#### 4.1 .env.example
- [ ] Add `CHAINLIT_PORT=8002`
- [ ] Add `CHAINLIT_API_KEY=your-api-key-here`
- [ ] Update `CORS_ORIGINS` comment with Chainlit URL example

#### 4.2 pyproject.toml
- [ ] Add `chainlit>=2.4.0` to dependencies

### 5. CORS Backend Configuration

#### 5.1 Documentation
- [ ] Document CORS requirement in plan/spec
- [ ] Ensure .env.example shows how to add Chainlit origin

## Task Dependencies

```
1.1 Core Setup
    │
    ├──▶ 1.2 SSE Client
    │        │
    │        └──▶ 1.3 Event Handlers
    │                  │
    │                  └──▶ 1.4 Main App
    │
    └──▶ 2.x Chainlit Config
    │
3.x Docker Config ──────▶ 4.x Environment Config
```

## Estimated Task Count

| Category | Tasks |
|----------|-------|
| Core Module | 4 |
| SSE Client | 4 |
| Event Handlers | 5 |
| Main Application | 3 |
| Chainlit Config | 2 |
| Docker | 2 |
| Environment | 3 |
| **Total** | **23** |

## Execution Order

1. **Phase 1 - Foundation**: Core module setup, constants, config
2. **Phase 2 - SSE Client**: Stream parsing, retry logic
3. **Phase 3 - Handlers**: on_chat_start, on_message implementation
4. **Phase 4 - Main App**: Wire everything together
5. **Phase 5 - Configuration**: Chainlit config, docker-compose
6. **Phase 6 - Environment**: .env.example, pyproject.toml

## Verification Checkpoints

- [ ] Chainlit starts without errors
- [ ] Chat sends message to FastAPI backend
- [ ] SSE tokens stream to UI
- [ ] Tool calls display with name only
- [ ] Errors show human-readable messages
- [ ] Auto-retry works on transient failures
- [ ] Docker Compose starts all services
