# AI-IEOS — Architecture
> AI International Education Orchestration System
> MVP: Japan graduate school; designed for global extension.

## 0. Thesis

**Rule First, LLM Second.**

The novelty of this system is not RAG, not the chatbot, not even the agent.
It is the **closed loop of**:

    Rule Engine  +  RAG  +  Agent  +  Recommendation

Most student projects look like: ChatBox -> RAG -> end. Hallucinations everywhere.
We invert: deterministic rules eliminate the impossible first, the LLM only
explains, ranks, and plans within the legal set; a post-check rejects any
hallucinated school the LLM still tried to slip in.

## 1. Five-Layer Overview

```
+---------------------------------------------------------------+
| 1. Frontend (Next.js 15 + React 19 + Shadcn UI + Tailwind)    |
|    Chat / Recommend / Timeline / Radar  (C-end only for MVP)  |
+--------------------------------+------------------------------+
                                 | HTTPS REST / SSE
+--------------------------------v------------------------------+
| 2. Backend & Orchestration (SpringBoot 3 + LangChain4j)       |
|   REST API | JWT Auth | 1 main Agent w/ Function Calling      |
+------+--------------+-----------+--------------+--------------+
       |              |           |              |
       |     +--------v-----+ +---v-----+ +------v-------+
       |     | 3. Easy Rules| | 4. RAG  | | 4. LLM       |
       |     |  - prefilter | |  pgvect | |   DeepSeek   |
       |     |  - postcheck | |  HNSW   | |   (OpenAI    |
       |     +--------------+ +---------+ |    compat)   |
       |                                  +--------------+
+------v--------------------------------------------------------+
| 5. Storage                                                    |
|   PostgreSQL + pgvector    Redis 7                            |
|   - business tables (JPA)  - chat memory                      |
|   - document_chunks (HNSW) - rate limit (Bucket4j)            |
|   - call_log               - hot caches                       |
+---------------------------------------------------------------+
```

## 2. Layer Details

### 2.1 Frontend (C-end only)

- Framework: Next.js 15 + React 19 + TypeScript (already in repo).
- Styling: Tailwind + **Shadcn UI** (kebab-case CLI: `npx shadcn@latest init`).
- Streaming: native `fetch` + ReadableStream (already in `lib/api.ts`).
- State: Zustand (already in repo).
- Charts: Recharts for radar + timeline.
- **No AntD, no admin console in MVP.** Data maintained via SQL / Excel import.

### 2.2 Backend & Orchestration (SpringBoot 3 + LangChain4j)

| Concern         | Choice                                             |
|-----------------|----------------------------------------------------|
| Framework       | Spring Boot 3.3, JDK 21                            |
| Security        | Spring Security 6 + JWT (jjwt)                     |
| ORM             | Spring Data JPA + Hibernate                        |
| Migrations      | Flyway                                             |
| Validation      | Jakarta Bean Validation                            |
| API docs        | springdoc-openapi                                  |
| Rate limit      | Bucket4j + Redis (global 100/min, user 60/min)     |
| AI orchestration| LangChain4j 0.36+ (`AiServices`, `@Tool`)          |
| Stream output   | Servlet `ResponseBodyEmitter` (SSE)                |

LangChain4j gives us four things we would otherwise hand-roll:
1. Provider abstraction (`ChatLanguageModel`)
2. Chat memory (we plug in `RedisChatMemoryStore`)
3. Tool / Function Calling glue
4. Embedding + `PgVectorEmbeddingStore`

### 2.3 Rule Engine — Easy Rules

Two responsibilities only:

1. **Pre-filter**: input `StudentProfile`, output the legal candidate pool.
2. **Post-check**: input `List<Recommendation>` from the LLM, drop any that
   violate hard thresholds (defends against hallucinations).

Rule format (MVP): JSON files under `backend/src/main/resources/rules/`.
Hot reload via `POST /api/v1/admin/rules/reload`. Versioning = git history.

Hard requirements stored per `Program`:
- `gpa_min` (with `gpa_scale` so 4.0 / 5.0 / 100 all work)
- `lang_type` in {TOEFL, IELTS, JLPT}
- `lang_score_min`

Internal normalization: everything converted to GPA-on-4.0 before comparison.

### 2.4 RAG Engine

```
PDF / HTML
   |  Apache Tika
   v
plain text
   |  DocumentSplitter recursive(1000, 200)
   v
chunks
   |  OpenAI text-embedding-3-small (1536d)
   v
PgVectorEmbeddingStore -> document_chunks (HNSW cosine)
```

Same schema as the legacy Python service, so existing vectors stay valid.
No GraphRAG, no knowledge graph.

### 2.5 LLM Provider Layer

- **MVP: DeepSeek only** (`deepseek-chat`, `deepseek-reasoner`).
- All calls go through LangChain4j's `OpenAiChatModel` pointed at
  `https://api.deepseek.com/v1` — this *is* the abstraction. Adding GPT-4o
  later is one bean + one base URL change. No fallback chain, no provider
  manager bean soup.
- Embeddings: OpenAI `text-embedding-3-small` (kept on OpenAI because
  DeepSeek does not ship embeddings; this is the only OpenAI key required).

### 2.6 Storage

| Engine                   | Role                                          |
|--------------------------|-----------------------------------------------|
| PostgreSQL 16 + pgvector | Business tables + `document_chunks` (HNSW)    |
| Redis 7                  | Chat memory, rate limit counters, hot caches  |

Schema includes forward-looking fields (`region`, `system_type`, `gpa_scale`)
but MVP only populates Japan rows.

## 3. The One Agent

A single `IeosAdvisorAgent` (LangChain4j `@AiService`). No multi-agent
choreography. The agent has exactly **5 tools**:

| Tool                       | Input            | Output                              |
|----------------------------|------------------|-------------------------------------|
| `extractProfile`           | free text        | structured `Profile`                |
| `ruleEngineFilter`         | `Profile`        | `List<UniversityId>` (legal pool)   |
| `ragSearch`                | query, k         | `List<Snippet>` from policy corpus  |
| `matchAndCategorize`       | profile, pool    | reach / target / safety buckets     |
| `validateRecommendations`  | profile, recs    | recs minus rule violations (postcheck)|

The agent decides the order at runtime via Function Calling; the system
prompt nudges the canonical path:

```
extractProfile -> ruleEngineFilter -> ragSearch -> matchAndCategorize
                                                        |
                                            validateRecommendations
                                                        |
                                                 generateTimeline (inline)
```

`generateTimeline` is **not** a tool — it is just a final templated LLM
call once the agent has settled on the recommendation set, so we keep the
tool surface to five.

## 4. End-to-End Trace

User: "I'm a software engineering junior, GPA 1.22/5, want a Japanese
master's in AI, plan it for me."

| #  | Component              | Action                                              |
|----|------------------------|-----------------------------------------------------|
| 1  | React (Shadcn)         | `POST /api/v1/agent/plan/stream` (SSE)              |
| 2  | Spring Controller      | parse JWT -> userId                                 |
| 3  | RedisChatMemoryStore   | load history for `chat:memory:{userId}`             |
| 4  | LangChain4j Agent      | sees the message, picks tools                       |
| 5  | extractProfile         | -> `{gpa:1.22, scale:5, target:"AI", region:"JP"}`  |
| 6  | ruleEngineFilter       | normalize to 4.0 (=0.98), prune to GPA-tolerant pool|
| 7  | ragSearch              | retrieve "JP master's in AI" policy snippets        |
| 8  | matchAndCategorize     | bucket into reach / target / safety                 |
| 9  | validateRecommendations| drop anything LLM hallucinated above thresholds     |
| 10 | LLM final pass         | write timeline + reasoning, stream tokens           |
| 11 | Controller             | `data: {...}\n\n` SSE -> typewriter UI              |
| 12 | Postgres (async)       | persist `recommendation` rows + `call_log`          |

## 5. Target Repository Layout

```
japan-uni-assist/
  docker-compose.yml
  docs/
    ARCHITECTURE.md        <-- this file
    ROADMAP.md
  frontend/                  Next.js, kept and refactored
    src/app/
      chat/                  Shadcn
      recommend/             Shadcn
      timeline/              new, Shadcn + Recharts
      radar/                 new, Shadcn + Recharts
  backend/                   SpringBoot, replaces legacy NestJS + FastAPI
    pom.xml
    src/main/java/io/ieos/
      IeosApplication.java
      config/                Security, CORS, Redis, Bucket4j
      domain/                JPA entities
      repository/            Spring Data interfaces
      service/               business services
      controller/            REST + SSE
      ai/
        provider/            ChatLanguageModel beans
        agent/               @AiService interface
        tool/                @Tool methods (the 5 tools)
        rag/                 ingestion + PgVectorEmbeddingStore
        memory/              RedisChatMemoryStore
      rule/                  Easy Rules wrapper + DSL loader
    src/main/resources/
      application.yml
      db/migration/          Flyway V1__init.sql ...
      rules/                 jp-master.json (MVP, ~30 rules)
  scripts/
    import_universities.py   Excel/CSV -> DB seeder
    ingest_documents.py      PDF folder -> /api/v1/rag/documents
  _archive/                  Legacy code, kept for fallback
    nestjs-backend/
    fastapi-ai-service/
```

## 6. Non-Goals (Explicit)

The following are intentionally **out of scope** for MVP:

- Multi-provider fallback chain. One provider (DeepSeek) only.
- Multi-agent choreography. One agent, five tools.
- Admin console (B-end). Use SQL / Excel scripts.
- Drools. Easy Rules is enough for "GPA >= 2.3" / "JLPT >= N2".
- GraphRAG / knowledge graph. Relational + vector covers the domain.
- Cost dashboards. A flat `call_log` table is all we need for the demo.

## 7. Design Principles (cheat sheet)

1. **Schema is forward-compatible**, content is Japan-only.
2. **Rules are fixed in interface, swappable in engine** (Easy Rules now,
   Drools later if real customers demand it).
3. **The LLM never escapes the rules** — every recommendation passes
   `validateRecommendations` before reaching the user.
4. **Streaming is default**, sync endpoints are fallback only.
5. **Old system stays alive** under `_archive/` for the whole MVP window.
