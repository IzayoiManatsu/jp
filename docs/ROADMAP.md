# AI-IEOS — Roadmap

> Strangler-fig migration: legacy NestJS + FastAPI move to `_archive/`, new
> SpringBoot grows beside them, frontend cuts over by route.
> MVP target: ~3 weeks (15 working days) for one developer.

## Sequence at a Glance

```
day  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
P0   X
P1      X  X  X
P2               X  X
P3                     X  X
P4                            X
P5                               X  X  X
P6                                       X  X
P7                                             X  X
```

| Phase | Days | Theme                                             |
|-------|------|---------------------------------------------------|
| P0    | 1    | Freeze + archive + scaffold                       |
| P1    | 3    | SpringBoot data layer + auth                      |
| P2    | 2    | DeepSeek provider via LangChain4j                 |
| P3    | 2    | RAG on pgvector                                   |
| P4    | 1    | Easy Rules engine                                 |
| P5    | 3    | Single Agent + 5 Tools                            |
| P6    | 2    | Shadcn UI refactor + new pages (timeline, radar)  |
| P7    | 2    | E2E, smoke load, DNS cutover                      |

## P0 — Freeze and Scaffold (1 day)

**Goal**: clean workspace, irreversible decisions written down.

- Move legacy code: `git mv japan-uni-assist/backend _archive/nestjs-backend`,
  `git mv japan-uni-assist/ai-service _archive/fastapi-ai-service`.
- Create empty `japan-uni-assist/backend/` (Maven, JDK 21, `pom.xml`).
- Update `docker-compose.yml`: drop `ai-service`, replace `backend` with new
  Java image; keep `postgres`, `redis`, `frontend`.
- Land `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` (this file).
- Commit on a branch `feat/ieos-migration`, **not** main.

**Exit criteria**: `docker compose up postgres redis frontend` still works
against legacy backend pulled from `_archive/` (so we can still demo).

## P1 — Data Layer + Auth (3 days)

**Goal**: SpringBoot can talk to the same Postgres the old system uses.

- `pom.xml` deps: `spring-boot-starter-web`, `-data-jpa`, `-security`,
  `-validation`, `flyway-core`, `postgresql`, `jjwt-api/-impl/-jackson`,
  `bucket4j-redis`, `pgvector` (driver helper).
- Flyway `V1__init.sql`: translate Prisma schema 1:1. Add forward fields:
  - `universities.region` (default `'JP'`), `universities.system_type`
  - `programs.gpa_min`, `programs.gpa_scale`, `programs.lang_type`,
    `programs.lang_score_min` (hard requirements live on the program row,
    not as JSON, so the rule engine can index them).
  - `call_log` table: `id, user_id, route, model, prompt_tokens,
    completion_tokens, latency_ms, created_at`.
- JPA entities mirroring the schema; `@Convert` for JSON columns.
- Spring Security config: stateless, JWT filter, `BCryptPasswordEncoder`
  configured at strength 10 (matches legacy `$2b$10$` hashes -> existing
  users log in unchanged).
- Controllers up: `/api/v1/auth/register|login`, `/api/v1/users/me`,
  `/api/v1/universities`.
- Bucket4j `@RateLimit` annotation + Redis-backed bucket store.
- springdoc-openapi: serve `/docs` (drop-in replacement for the old Swagger).

**Exit criteria**: register a new user via curl, log in, hit
`/api/v1/universities` with the bearer token, get the seeded list.

## P2 — DeepSeek Provider via LangChain4j (2 days)

**Goal**: replace the Python provider zoo with one bean.

- Deps: `langchain4j-bom`, `langchain4j-spring-boot-starter`,
  `langchain4j-open-ai`.
- `ChatLanguageModel` bean: `OpenAiChatModel.builder().baseUrl(
  "https://api.deepseek.com/v1").modelName("deepseek-chat").apiKey(env).build()`.
- `StreamingChatLanguageModel` bean: same pattern.
- `EmbeddingModel` bean: `OpenAiEmbeddingModel` with the real OpenAI key
  (DeepSeek has no embeddings). `text-embedding-3-small`, 1536d.
- `ChatService`: thin wrapper that records `call_log` rows around model
  invocations and exposes:
  - `POST /api/v1/ai/chat` (sync)
  - `POST /api/v1/ai/chat/stream` (SSE via `ResponseBodyEmitter`)
- Test: ask "hello" sync + stream, observe `call_log` populated.

**Exit criteria**: a streamed answer reaches a curl client and a row lands
in `call_log` with token counts.

## P3 — RAG on pgvector (2 days)

**Goal**: queries against existing vectors yield the same hits as the
legacy Python service.

- Bean: `EmbeddingStore<TextSegment> store = PgVectorEmbeddingStore.builder()
  .host(...).port(5432).database(...).user(...).password(...)
  .table("document_chunks").dimension(1536).useIndex(true)
  .indexListSize(100).build();`
- Ingestion pipeline (`IngestionService`):
  - `ApacheTikaDocumentParser` (PDF / HTML / TXT)
  - `DocumentSplitters.recursive(1000, 200)`
  - `EmbeddingStoreIngestor` writes through the bean above
- Query: `EmbeddingStoreContentRetriever` with `maxResults=8`,
  `minScore=0.7`.
- Controllers:
  - `POST /api/v1/rag/documents` (admin only): upload + ingest
  - `POST /api/v1/rag/query` (sync, returns hits + similarity)
- Cross-check: pick 5 queries that worked in the old FastAPI, confirm
  identical top hits.

**Exit criteria**: parity test passes; ingestion of a new PDF visible in
`document_chunks` within seconds.

## P4 — Easy Rules Engine (1 day)

**Goal**: deterministic filter that the Agent can call as a tool.

- Dep: `org.jeasy:easy-rules-core` + `easy-rules-mvel`.
- Domain:
  - `HardRequirement { gpaMin, gpaScale, langType, langScoreMin }`
    (already on `programs` table from P1)
  - `RuleDecision { passed: boolean, reasons: List<String> }`
- `RuleEngineService`:
  - `filter(Profile p, List<Program> pool) -> List<Program>` — keep only
    those passing every hard requirement after unit normalization
  - `validate(Profile p, List<Recommendation> recs) -> List<Recommendation>`
    — drop violators (used as the post-check on LLM output)
- `GpaNormalizer`: 4.0 / 5.0 / 100 -> internal 4.0.
- JSON rule files in `src/main/resources/rules/jp-master.json` for the
  ~30 starter rules. Reload endpoint: `POST /api/v1/admin/rules/reload`.
- Unit test: profile `{gpa:1.22, scale:5}` against UTokyo CS (gpa_min 3.5)
  -> rejected with reason.

**Exit criteria**: green test suite proving filter + validate behavior.

## P5 — Single Agent + 5 Tools (3 days)

**Goal**: the architecture's centerpiece.

- Define `IeosAdvisorAgent`:

  ```java
  public interface IeosAdvisorAgent {
      TokenStream plan(@MemoryId String sessionId,
                       @UserMessage String input);
  }
  ```

- System prompt: instruct strict pipeline order, force Chinese output,
  cite RAG sources, never recommend a school not in the legal pool.
- Five tools (each a Spring bean method annotated `@Tool`):
  1. `extractProfile(String freeText) -> Profile`
  2. `ruleEngineFilter(Profile) -> List<UniversityId>`
  3. `ragSearch(String query, int k) -> List<Snippet>`
  4. `matchAndCategorize(Profile, List<UniversityId>) -> List<Recommendation>`
  5. `validateRecommendations(Profile, List<Recommendation>) -> List<Recommendation>`
- `RedisChatMemoryStore implements ChatMemoryStore`: serialize messages
  as JSON, key `chat:memory:{sessionId}`, TTL 7 days.
- Wire with `AiServices.builder(IeosAdvisorAgent.class)
    .streamingChatLanguageModel(model)
    .chatMemoryProvider(id -> MessageWindowChatMemory.builder()
        .id(id).maxMessages(20).chatMemoryStore(redisStore).build())
    .tools(extractProfileTool, ruleFilterTool, ragTool,
           matchTool, validateTool)
    .build()`.
- Controller: `POST /api/v1/agent/plan/stream` -> `ResponseBodyEmitter`.
- Persist final recommendations to `recommendation` table after the stream
  closes (mirror of legacy behavior).
- Fallback: if the agent throws or stalls > 30s, the controller catches and
  routes to a non-agent `RecommendService.singleShot(profile)` that mimics
  the legacy Python recommender. User never sees a blank screen.

**Exit criteria**: the end-to-end trace in `ARCHITECTURE.md` section 4
works on a real profile; rule violations are demonstrably caught by the
post-check (inject a deliberately bad LLM response in a unit test).

## P6 — Frontend Refresh (2 days)

**Goal**: minimal, scoped UI upgrade. No AntD, no admin pages.

- `npx shadcn@latest init` inside `frontend/` (uses Tailwind already there).
- Pull components: `button`, `card`, `input`, `textarea`, `scroll-area`,
  `avatar`, `badge`, `dialog`, `separator`, `skeleton`.
- Refactor `app/chat/page.tsx`: replace ad-hoc classNames with Shadcn
  `Card` + `Avatar` + `ScrollArea`. Keep the existing `streamChat` logic
  in `lib/api.ts`.
- Refactor `app/recommend/page.tsx`: Shadcn `Form` (`react-hook-form` is
  already in `package.json`).
- New `app/timeline/page.tsx`: vertical timeline driven by the agent's
  final response, dates parsed from a small JSON block the prompt
  instructs the LLM to emit at the end.
- New `app/radar/page.tsx`: Recharts radar of {GPA, language, research,
  projects, activities, motivation}.
- Update `lib/api.ts` base URL via `NEXT_PUBLIC_API_URL`; point at new
  SpringBoot. Add `/api/v1/agent/plan/stream` client.

**Exit criteria**: visual sweep on the four pages; SSE still streams; no
console errors.

## P7 — E2E, Smoke Load, Cutover (2 days)

- Playwright E2E: register -> create profile -> agent plan -> appears in
  history -> follow-up question in chat.
- k6 smoke: 50 concurrent SSE clients for 3 minutes, hold p95 latency
  under target.
- Flip `NEXT_PUBLIC_API_URL` in production env; scale legacy NestJS to 0;
  keep `_archive/` and DB backups for two weeks.
- Tag `v0.1.0-mvp`.

## Risk Register (post-cut)

| ID | Risk                                          | Mitigation                       |
|----|-----------------------------------------------|----------------------------------|
| R1 | Java unfamiliarity slows P1-P2                | Lean on Spring starters; copy from samples |
| R2 | LangChain4j 0.36 API drift                    | Pin version in `pom.xml`         |
| R3 | bcrypt cross-language hash compatibility      | P1 includes a parity test        |
| R4 | DeepSeek function-calling quirks              | System prompt is explicit about JSON tool args; fall back to legacy single-shot recommender |
| R5 | RAG parity with legacy hits                   | P3 cross-check on 5 queries      |
| R6 | SSE buffering on reverse proxies              | Disable `nginx` proxy_buffering on `/agent/plan/stream` |

## What This Roadmap Deliberately Does Not Do

- No admin console. Data entry = `scripts/import_universities.py` reading
  an Excel file maintained by hand. This is a thesis project, not an ERP.
- No multi-provider fallback. One key, one model, one bean.
- No Drools. If a real customer ever asks for hot-swappable rule packs
  with audit trails, swap the engine behind `RuleEngineService` then.
- No multi-agent system. One agent, five tools. Function Calling is the
  story; "multi-agent" adds slides, not value.
- No GraphRAG. Relational + vector covers everything from program rules
  to professor research areas.

## Definition of Done (MVP)

The system is "done" when a panel of three reviewers, given a fresh
student profile, can:

1. Submit it through the Shadcn UI.
2. Watch tokens stream while the agent narrates which tool it is calling.
3. See a recommendation list where every entry satisfies the hard
   requirements (proven by a side-by-side rule check on screen).
4. Read a six-month timeline grounded in the policy snippets retrieved
   from RAG.
5. Ask a follow-up question and have the agent remember the profile.

That is the demo. Everything beyond it is a non-goal for this milestone.
