# AGENTS.md

> Core architectural context and strict engineering guardrails for AI coding agents working on the **Realtime Speech-to-Speech & Speech-to-Text Translation System**. Keep this file concise; consult the specific specification files below via progressive disclosure.

## 1. Progressive Disclosure (Specification Routing)

DO NOT read all specification files at once. Read ONLY the document relevant to your current task:

| When working on... | MUST read specification |
| :--- | :--- |
| Implementation Roadmap, 10 Execution Phases & Granular Task Breakdown (`TASK-DB-01` .. `TASK-HA-04`) | [implementation-tasks-roadmap.md](file:///D:/code/ws-translation-realtime/docs/tasks/implementation-tasks-roadmap.md) |
| 10s micro-billing formula, Stripe/VietQR top-up, cost optimization rules (VAD, TTS), Host/Listener permissions | [01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md) |
| Detailed business logic & Acceptance Criteria for all 38 features (`FR-101` .. `FR-604`) | [02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md) |
| AWS Single-AZ architecture, Redis keys, 6 DynamoDB tables, Failover/Handover, Docker & GitHub Actions CI/CD | [03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md) |
| Monorepo structure, REST API (`/api/v1/*`), WebSocket JSON payloads, S3 schemas (`master.json`, `summary.json`), 6 UI screens | [04-api-websocket-and-ui-specs.md](file:///D:/code/ws-translation-realtime/docs/specs/04-api-websocket-and-ui-specs.md) |

---

## 2. Tech Stack & Core Architecture

- **Frontend (`apps/web`)**: Next.js 15 (App Router, TypeScript, `output: "standalone"`), TailwindCSS, Shadcn UI, WebAudio (`AudioWorklet` + Silero VAD), AWS AppSync Events WebSocket Client.
- **Backend (`apps/backend`)**: Python 3.12+, **FastAPI**, **Uvicorn (`uvloop` + `httptools`)**, **Pydantic v2**, package management via **`uv`**. Consolidates REST API (`/api/v1/*`), WebSocket Audio Ingest (`/ws/v1/*`), and Async Background Workers in a single unified service.
- **Database & State**:
  - **PostgreSQL 16 (Primary ACID Database)**: 9 relational tables (`users`, `user_profiles`, `wallets`, `payment_transactions`, `custom_vocabularies`, `promo_codes`, `promo_redemptions`, `rooms`, `room_transcripts` [metadata & S3 keys], `usage_ledger`). Handled via **SQLAlchemy 2.0 Async (`asyncpg`)** and **Alembic** migrations.
  - **ElastiCache for Redis (Single-AZ)**: 10s Audio Ring Buffer (`STREAM`), active TTS listener counter (`tts_count`), ephemeral live session transcript buffer.
  - **Amazon S3**: Permanent transcript package storage (`master.json`, `.txt`, `.srt`, `.vtt`, `.csv`), AI summaries (`summary.json`), and 24h TTS audio chunks (`.mp3`).
- **AWS AI & Fan-out Pipeline**: Amazon Transcribe Streaming (STT) -> Amazon Translate (MT) -> Amazon Polly Neural (TTS) -> S3/CloudFront + AWS AppSync Events (Fan-out up to 1,000 listeners/room). On-demand meeting summaries use **Amazon Bedrock** (`Claude 3.5 Haiku` / `Nova Lite`).
- **Deployment**: GitHub Actions (AWS OIDC) -> Build 2 separate Docker images (`web` & `backend`) -> Push to **Amazon ECR** -> Rolling deploy to 2 **Amazon ECS Fargate** services behind a single ALB in `ap-southeast-1a`.

---

## 3. Monorepo Layout

```text
ws-translation-realtime/
├── .github/workflows/ci-cd.yml       # CI/CD: Path filter (apps/web vs apps/backend) -> ECR -> ECS
├── apps/
│   ├── web/                          # Next.js 15 Standalone Docker (Port 3000)
│   │   ├── src/app/                  # UI Screens SCR-01..SCR-06
│   │   ├── src/worklets/             # AudioWorklet PCM 16kHz + Local Ring Buffer (5s) + VAD
│   │   └── src/lib/                  # API Client, AppSync Subscriber, Adaptive Audio Queue
│   └── backend/                      # FastAPI + asyncio/uvloop Docker (Port 8000)
│       ├── alembic/                  # Database schema migrations (asyncpg)
│       ├── app/
│       │   ├── main.py               # Entrypoint (/api/v1, /ws/v1, Lifespan background tasks)
│       │   ├── api/                  # Routes (auth, rooms, wallets, transcripts, health) & deps.py
│       │   ├── core/                 # config.py, db.py (async engine), security.py, exceptions.py
│       │   ├── models/               # SQLAlchemy 2.0 ORM Models (9 PostgreSQL tables)
│       │   ├── schemas/              # Pydantic v2 Models & Binary Audio protocol
│       │   ├── services/             # Business Logic (auth, rooms, billing, transcripts)
│       │   ├── integrations/         # AWS Clients (Cognito, S3, Transcribe, Translate, Polly, Bedrock, AppSync)
│       │   ├── ws/                   # Binary Audio Ingest, 500ms ACK, SIGTERM Handover
│       │   └── workers/              # Asyncio tasks: 10s Micro-Billing & S3 Transcript Compiler
│       └── tests/                    # pytest + pytest-asyncio + mocks
├── infra/                            # Terraform Multi-Environment Stacks (dev, staging, prod)
└── docker-compose.yml                # Local dev: web + backend + postgres + redis
```

---

## 4. Strict Engineering Guardrails

### 4.1. Async I/O & Concurrency in FastAPI
- **NO Blocking I/O inside `async def`**: Never use synchronous `boto3`, `requests`, `time.sleep()`, or synchronous `redis.Redis` inside the event loop.
- **Required Async Libraries**:
  - Database: `sqlalchemy.ext.asyncio` + `asyncpg`.
  - STT: `amazon-transcribe` (native `asyncio` HTTP/2 streaming).
  - AWS Services (S3, Translate, Polly, Bedrock, Cognito, AppSync): `aioboto3` / `aiobotocore`.
  - Redis: `redis.asyncio`.
  - External HTTP: `httpx.AsyncClient`.
- **Parallel N-Language Translation (`FR-304`)**: Always use `await asyncio.gather(*tasks)` when translating a segment into $N$ target languages to keep total MT latency `< 150ms`.

### 4.2. Byte-Level Binary Protocol & Zero-Downtime Failover
- **16-byte Binary Audio Header (Big-Endian `>IQBBH`)**:
  - Python unpack/pack: `seq_id, timestamp_ms, codec, flags, _ = struct.unpack(">IQBBH", frame[:16])` (4 + 8 + 1 + 1 + 2 = 16 bytes), followed by `audio_payload = frame[16:]`.
  - TypeScript `DataView`: `getUint32(0, false)`, `getBigUint64(4, false)`, `getUint8(12)`, `getUint8(13)`, `getUint16(14, false)`.
- **Redis Ring Buffer & S3 Transcript Pipeline (`FR-302`, `FR-306`)**: Append every incoming audio frame to Redis Stream `room:{roomId}:audio_buffer` (`MAXLEN ~ 100`). When a `Final` segment completes, update `last_committed_seq`, trim older frames, and store live sentences in Redis List `room:{roomId}:live_transcripts`. When room ends, compile to S3 (`master.json`, `.txt`, `.srt`, `.csv`) and record S3 key in PostgreSQL `room_transcripts`.
- **Graceful Handover (`FR-602`)**: On `SIGTERM`, mark the worker state as `DRAINING`, wait for the current utterance to reach `Final`, then send `{"event": "PREPARE_HANDOVER"}` before closing the WebSocket.

### 4.3. Cost Protection & Atomic Billing
- **Demand-Driven TTS (`FR-305`)**: Only invoke Amazon Polly for language `lang` if `HGET room:{roomId}:tts_count {lang} > 0`.
- **Partial Debounce (`FR-304`)**: Throttle `Partial` translations to at most once every `300ms` (or when $\ge 3$ new words are added).
- **Idempotent Billing & Webhooks (`FR-502`, `FR-506`)**:
  - Deduct 10s usage atomically via PostgreSQL transaction (`UPDATE wallets SET balance = balance - :cost ...` with `INSERT INTO usage_ledger`).
  - Payment webhooks MUST verify `HMAC-SHA256` signatures and enforce PostgreSQL `payment_transactions.transaction_id` unique constraint to prevent double-crediting.
  - Exclude any audio frames or characters from billing metrics if an AWS AI service returns a `5xx` error.
- **On-Demand AI Summary (`FR-407`)**: Only the Host can trigger `POST /api/v1/transcripts/{roomId}/summary`. Check `summary_status == "READY"` on PostgreSQL first; return cached `summary_s3_key` for free (`$0`) if present. Otherwise, invoke Bedrock once, save to S3 (90-day retention), update `room_transcripts`, and deduct the Host's wallet once.

### 4.4. Local Development & Offline Testing Strategy
- Wrap all external AWS AI/Event services (`Transcribe`, `Translate`, `Polly`, `Bedrock`, `AppSync`) in `app/integrations/`.
- When `ENV=local` or `ENV=test` (no real AWS credentials), automatically inject mock clients and use `fakeredis` + local PostgreSQL container so the entire E2E flow and `pytest` suite run 100% offline.

---

## 5. Mandatory Verification Commands

Always run the corresponding verification suite before claiming a task is complete:

```bash
# Backend (apps/backend)
cd apps/backend
uv run ruff check .                  # Linter
uv run mypy app                      # Typecheck
uv run pytest -v                     # Async Unit & Integration Tests

# Frontend (apps/web)
cd apps/web
pnpm lint                            # ESLint
pnpm typecheck                       # tsc --noEmit
pnpm test --run                      # Vitest
pnpm build                           # Next.js Standalone Build

# Docker Build (When modifying Dockerfiles or packaging config)
docker build -t ws-translation/backend:test ./apps/backend
docker build -t ws-translation/web:test ./apps/web
```

---

## 6. Language, Code Style & Git Conventions

- **Language Override (Project-level rule overriding global defaults)**:
  - **User Communication**: Communicate with the user in **Vietnamese** (keep technical terms in English).
  - **Code Comments & Docstrings**: ALWAYS write in **English** (explain `WHY`, not `WHAT`).
  - **Code Identifiers**: Write all variables, functions, classes, filenames, API paths, and JSON/DB keys in **English** (`snake_case` for Python, `camelCase` / `PascalCase` for TypeScript and JSON).
- **Git & Commit Conventions**:
  - **Commit Messages**: ALWAYS write in **English** and strictly follow **Conventional Commits** (`<type>(<scope>): <subject>`, e.g., `feat(backend): add 10s micro-billing worker`, `fix(web): handle websocket handover event`, `docs(specs): update dynamodb schema`). Allowed types: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`.
  - **NO AI Attribution / Co-Author**: STRICTLY FORBIDDEN to add `Co-Authored-By:` trailers, AI signatures, or any "Generated with..." taglines to commit messages or pull requests.
  - **NEVER Commit Brainstorming or Implementation Plans**: Files under `docs/superpowers/`, `docs/plans/`, or any brainstorming/implementation plan artifacts MUST NEVER be staged or committed to Git.
  - **Explicit Trigger**: Never run `git commit` or `git push` unless explicitly instructed by the user. Never use `git add .` (stage specific files only).
- **Security**:
  - Never hardcode or log secrets, tokens, or API keys.
  - In GitHub Actions workflows (`.github/workflows/*.yml`), ALWAYS pin third-party actions to a full 40-character commit SHA (with a version comment, e.g., `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`), never use mutable tags like `@v4` or `@v5`.
