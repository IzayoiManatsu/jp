# AI-IEOS — Architectural Decision Log

Short, immutable record of why we chose what we chose. New entries on top.

---

## ADR-001 — Rule First, LLM Second (2026-06-04)

**Decision**: deterministic rule engine sits in front of and behind every
LLM recommendation.

**Context**: most student "AI for study abroad" projects degenerate into
ChatBox -> RAG -> hallucination. The defensible novelty here is the
closed loop Rule Engine + RAG + Agent + Recommendation.

**Consequences**: the LLM may never recommend a school not in the legal
pool. The post-check `validateRecommendations` is mandatory in P5.

---

## ADR-002 — Easy Rules, not Drools (2026-06-04)

**Decision**: Easy Rules 4.x for MVP.

**Why**: the actual rules are shapes like "GPA >= 2.3", "JLPT >= N2".
Drools is built for insurance / banking / risk control workflows with
hot-swappable rule packs and audit trails — none of which an MVP needs.

**Reversibility**: the `RuleEngineService` interface is stable; swapping
to Drools later is internal.

---

## ADR-003 — DeepSeek only, no provider fallback chain (2026-06-04)

**Decision**: one `ChatLanguageModel` bean pointed at DeepSeek's
OpenAI-compatible endpoint.

**Why**: the demo audience does not care about provider diversity.
Multi-provider code pays in adapters, token accounting and tests; it
earns nothing in the rubric.

**Reversibility**: adding a second provider is one bean + a routing
service; no schema change.

---

## ADR-004 — One Agent, five tools (2026-06-04)

**Decision**: a single `IeosAdvisorAgent` (LangChain4j `@AiService`) with
exactly five `@Tool` methods. No planner-agent / executor-agent split.

**Why**: Function Calling is already the impressive concept; multi-agent
choreography multiplies complexity without changing the demo outcome.

---

## ADR-005 — No admin console (B-end) in MVP (2026-06-04)

**Decision**: data entry is `scripts/import_universities.py` reading an
Excel file plus raw SQL. No AntD pages.

**Why**: a real admin covers universities, programs, professors, rules,
documents and users — that is an ERP, not a 3-day sprint. Build it after
the MVP earns a green light.

---

## ADR-006 — Strangler-fig migration (2026-06-04)

**Decision**: legacy `nestjs-backend/` and `fastapi-ai-service/` move to
`_archive/`, the new SpringBoot grows beside them, the old system stays
deployable as a fallback through the entire MVP window.

**Why**: Agent code has a real chance of regression; we keep a working
demo at all times.

---

## ADR-007 — Forward-compatible schema, Japan-only content (2026-06-04)

**Decision**: add `region`, `system_type`, `gpa_scale` columns from day
one (Flyway V1), but only populate Japan rows.

**Why**: changing the schema later for global expansion costs more than
adding three columns up front.
