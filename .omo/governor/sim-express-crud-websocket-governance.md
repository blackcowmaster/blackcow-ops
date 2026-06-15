# Governance Decision: sim-express-crud-websocket

| Field | Value |
|---|---|
| **Task** | Plan WebSocket real-time broadcast for task CRUD events (create/update/delete) using the `ws` library. Plan only — no implementation. |
| **Governed at** | 2026-07-14T20:00:00Z |
| **Detected Intent** | Feature |
| **Parent Governance** | `.omo/governor/sim-express-crud-implementation-governance.md` (FULL, completed — 39 tests, 7/7 gates pass) |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Plan-only task, like the original sim-express-crud governance. However, WebSocket is genuinely new tech for this codebase — no prior WebSocket artifacts exist. Uncertainty is HIGH due to: (a) Express 5.x compatibility with `ws` HTTP upgrade path, (b) WebSocket auth model (JWT over query params vs first-message), (c) broadcast architecture (shared event emitter vs direct `wss` reference), (d) connection lifecycle (ping/pong, reaping stale clients), (e) test strategy (supertest cannot test WebSocket — needs separate infra). STANDARD enables multi-lane exploration + adversarial review while avoiding FULL-mode over-orchestration for a plan-only artifact. |
| **Trust Level** | L1 | Plan-only, no code mutation. Reduced adversarial review scope (2 reviewers vs 3) since the plan is an architectural design document, not implementation. L2 would add adversarial review depth but the architectural decisions are constrained enough (single-resource CRUD, single-process broadcast) that 2 reviewers suffice. |
| **Bootstrap Lanes** | 5 | Express 5 WebSocket integration patterns, `ws` library API surface, WebSocket auth models (JWT), broadcast/event-emitter architecture, connection lifecycle + testing strategy |
| **PDCA Max Cycles** | 2 | Plan review/revision cycles. 2 cycles allows one round of reviewer findings incorporated. |
| **Adversarial Reviewers** | 2 | Medium scope — single architectural addition with 4 integration points (server, auth, broadcast, lifecycle). 2 reviewers catch blind spots without over-review. |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ✅ | Universal — must specify WebSocket test strategy (jest + `ws` client or `ws` mock) |
| M3 regression | ✅ | Existing 39 tests must remain green — plan must not alter REST behavior |
| M4 lint | ✅ | New `.ts` files in plan: WebSocket manager, server.ts modifications, controller changes |
| M5 dead-code | ❌ | No deletions expected — purely additive feature |
| S1 dataFlow | ✅ | New data path: Controller → EventEmitter → WebSocket broadcast → connected clients. Must not bypass auth or leak internal fields. |
| S2 auth | ✅ | WebSocket connections must authenticate. JWT over query params (common `ws` pattern) or first-message auth handshake. Must enforce same HS256 + expiry as REST. |
| S3 injection | ✅ | WebSocket messages are a new input surface. Broadcast payloads must be sanitized (no internal fields). Client→server messages (if any) must be validated. |
| P1 query | ❌ | No DB changes — broadcast triggered from existing service layer, no new queries |
| P2 memory | ✅ | WebSocket connections are stateful, long-lived. Plan must address: max connections, idle timeout (ping/pong), graceful reaping of stale clients, memory ceiling per connection. |
| P3 latency | ❌ | No p95 target specified for broadcast delivery |

**Active gates (8/11):** M1, M2, M3, M4, S1, S2, S3, P2

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O4 (browser available from capabilities.json) |
| **Browser Available?** | YES |
| **Capped?** | O4 → O2 (plan-only — no runtime verification possible) |
| **Fallback Strategy** | Plan verification via structural review: trace all 8 gates in plan text, cross-reference against `ws` library API, Express 5 documentation, and known WebSocket security patterns (OWASP). For WebSocket testing, specify `jest` + `ws` client approach (connect, authenticate, await message, verify payload). |
| **Residual Risk** | Plan cannot be runtime-verified against a live WebSocket server. Risk accepted — plan-only task. O4 browser capability unused; would be valuable for O3/O4 post-implementation verification (browser-based WebSocket client testing). |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 7 |
| Stage 3 | uncertainty ≥ 60 | 10 |

**Initial uncertainty estimate: 55/100.** Rationale:
- `ws` library API: LOW uncertainty (well-documented, mature)
- Express 5 + `ws` HTTP upgrade: HIGH uncertainty (Express 5 changed internal server handling; need to verify `server.on('upgrade')` pattern still works)
- WebSocket JWT auth: MEDIUM uncertainty (query-param pattern well-known but has security tradeoffs — token in URL logs)
- Broadcast architecture: MEDIUM uncertainty (EventEmitter vs direct reference tradeoffs)
- Connection lifecycle: MEDIUM uncertainty (ping/pong is standard but Express graceful-shutdown coordination with WebSocket is non-trivial)
- Test strategy: HIGH uncertainty (no existing WebSocket test infra; supertest incompatible)

This justifies progressive widening: if bootstrap lanes confirm Express 5 `upgrade` event works and test strategy firms up, uncertainty drops to <30 → Stage 1. If contradictions emerge, widening to 7 lanes at Stage 2.

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch D1 (pro) → plan re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles | ESCALATE |
| Scope creep | D2 flags scope change (e.g., rooms, multi-tenancy, horizontal scaling) | Return to planner |
| Express 5 incompatibility | Lane reports `upgrade` event broken or deprecated in Express 5 | ESCALATE — may require architectural pivot (standalone `http.Server` + `ws`) |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| FP-010 | P1 | `Date.toISOString()` drops microseconds, breaking keyset cursor pagination | 2026-06-27T12:00:00Z | 90 | Not applicable to WebSocket — no timestamp/cursor concerns in broadcast path |

**Feed rules:**
- `effectiveness ≥ 80` → apply known fix automatically before PDCA
- `effectiveness 40-79` → suggest fix, require confirmation
- `effectiveness < 40` → escalate gate priority, do NOT auto-apply (fix unreliable)
- `reappeared_after_fix: true` → mark pattern as CRITICAL, require architectural review

No failure patterns match the `websocket` task area. This is a genuinely new domain for this codebase — no prior patterns to learn from.

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~12K |
| **Tokens (bootstrap — 5 lanes)** | ~25K |
| **Tokens (plan writing)** | ~20K |
| **Tokens (QA — 8 gates)** | ~12K |
| **Total estimated** | ~69K |
| **Est. cost (flash)** | $0.010 |
| **Est. cost (pro)** | $0.031 |
| **Est. cost (blended)** | ~$0.020 |
| **Historical ROI** | 0.78 score/token (feature area, from loop-roi.jsonl) |
| **Budget utilization** | ~60% of STANDARD mode budget |
| **Recommendation** | PROCEED |

## Preflight Codebase Assessment

### Integration Points Identified

| Integration Point | Current State | WebSocket Impact |
|---|---|---|
| **`src/server.ts:13`** | `const server = app.listen(env.PORT, ...)` — creates `http.Server` but doesn't export it | Must export `server` so `ws.Server` can attach via `server.on('upgrade', ...)`. Graceful shutdown must close WebSocket connections before pool end. |
| **`src/controllers/tasks.controller.ts:31-48`** | `create`, `update`, `remove` — fire-and-forget service calls, no event emission | Must emit events after successful mutations. Controller is the right integration point (thin mapper, sees both request context and response). |
| **`src/services/tasks.service.ts:22-57`** | Service returns domain objects, no side effects | Could alternatively emit from service (better decoupling), but controller has request context (userId — needed for targeting? No — task is multi-tenant, broadcast to all). Service layer emission is architecturally cleaner. |
| **`src/middleware/auth.ts:20-57`** | JWT HS256 for HTTP requests only | WebSocket upgrade has no `Authorization` header — standard pattern is `?token=<jwt>` query param on connect. Auth middleware needs a non-HTTP variant or the `ws` `verifyClient` callback. |
| **`src/app.ts:1-38`** | Express app creation, no WebSocket awareness | Must pass the `http.Server` through (or create `ws.Server` externally and inject). Express 5's `app.listen()` wrapper may need to be bypassed. |
| **`src/types/task.ts:22-28`** | `TaskResponse` for REST responses | WebSocket broadcast payload should reuse `TaskResponse` (already sanitized — no `user_id`, no `deleted_at`). Add event envelope: `{ event: 'task.created' | 'task.updated' | 'task.deleted', data: TaskResponse, timestamp: string }`. |

### Express 5 Compatibility Concern

Express 5 (`^5.2.1` in package.json) changed the `app.listen()` internals. In Express 4, you could do:

```typescript
const server = http.createServer(app);
const wss = new WebSocketServer({ server });
server.listen(3000);
```

In Express 5, `app.listen()` returns an `http.Server` but the internal routing uses a different promise-based API. **Lane exploration must verify** that `server.on('upgrade', ...)` still fires correctly when the server is created via `app.listen()` vs `http.createServer(app)`. This is a HIGH-uncertainty item and justifies the progressive widening trigger.

### Existing Architecture Fit

The codebase follows a clean 3-layer architecture (Controller → Service → Repository). WebSocket broadcast is a **cross-cutting concern** — it should be injected as a dependency rather than hard-wired. Options:

1. **Option A — Controller emission**: Controller calls `wss.broadcast(event)` after `service.create()`. Simple, but couples controller to WebSocket.
2. **Option B — Service emission via EventEmitter**: Service emits `task.created` event, WebSocket manager listens. Cleaner separation, testable. Adds EventEmitter dependency to service.
3. **Option C — Repository emission**: Fires after DB write. Maximum consistency (only broadcast if DB confirmed) but mixes concerns.

**Recommendation to plan:** Prefer Option B (Service + EventEmitter) — aligns with the existing architecture's separation of concerns. Service already returns domain objects; adding an event emission does not break the contract.

## Architectural Risks (Pre-Discovery)

| Risk | Severity | Mitigation |
|---|---|---|
| Express 5 `upgrade` event not firing from `app.listen()` | HIGH | Lane must verify with minimal reproduction. Fallback: use `http.createServer(app)` + manual listen. |
| JWT in WebSocket query params — token in server logs | MEDIUM | Accept for now (single-process, no proxy). Document that production needs `Sec-WebSocket-Protocol` header-based auth behind a reverse proxy. |
| Broadcast to stale/closed connections → memory leak | MEDIUM | `ws` library emits `close` event. Plan must specify `ws.on('close')` cleanup + periodic `ws.ping()` heartbeat (30s interval). |
| Concurrent broadcast during high-throughput mutations | LOW | Node.js is single-threaded; `ws.send()` is async. Backpressure handled by `ws.bufferedAmount`. Plan should note this but no special mitigation needed for CRUD-scale traffic. |
| No WebSocket testing infrastructure | MEDIUM | Plan must specify `jest` + `ws` client approach. Integration test: start server, connect WebSocket, create task via REST, assert broadcast message received within timeout. |
| Client→server WebSocket messages (scope creep) | LOW | Plan must explicitly scope OUT — broadcast-only. No client→server commands. No chat, no rooms, no multi-tenancy routing. |

## Self-Audit Checklist (Pre-Emit)

- [x] Mode selection matches task scale (STANDARD for plan-only, not over-orchestrated)
- [x] Gate selection based on actual diff signals and codebase analysis (8 active gates)
- [x] Observable level achievable (O2 structural trace — plan-only, no runtime)
- [x] Failure-pattern feed loaded from memory (no matches for websocket area)
- [x] Loop ROI history consulted (0.78 score/token for feature area, PROCEED)
- [x] Escalation rules defined with concrete actions (Express 5 upgrade failure path)
- [x] Governance document written to `.omo/governor/sim-express-crud-websocket-governance.md`
- [x] No invented diff signals or failure patterns
- [x] Mode escalation justified by evidence (uncertainty 55/100 from Express 5 + auth + test unknowns)
- [x] Progressive widening policy defined with explicit trigger thresholds
- [x] Integration points traced from actual source code (file:line references)
