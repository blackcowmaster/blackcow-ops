# Governance Decision: input-sanitization

| Field | Value |
|---|---|
| **Task** | Add input sanitization to Express CRUD app: trim, HTML-escape, strip HTML tags, preserve emoji — at Zod schema level + utility function + tests |
| **Governed at** | 2026-06-16T00:00:00Z |
| **Detected Intent** | Security — XSS prevention / input sanitization hardening |

## Mode Selection

| Decision | Value | Rationale |
|---|---|---|
| **Mode** | STANDARD | Focused change: one schema file + one new utility + test file. Not trivially batchable (Zod transform integration requires careful ordering). Not complex enough for FULL. |
| **Trust Level** | L2 | Human should review sanitization logic — security-critical transformation on all user text inputs. |
| **Bootstrap Lanes** | 3 | (A) sanitize utility + unit tests, (B) Zod schema integration, (C) integration test verification |
| **PDCA Max Cycles** | 3 | 1 for implementation, 1 for test iteration, 1 for final verification |
| **Adversarial Reviewers** | 3 | M-size security task — 3 reviewers for XSS bypass attempts |

## Gate Selection

| Gate | Run? | Trigger Signal |
|---|---|---|
| M1 spec-match | ✅ | Universal |
| M2 test-pass | ✅ | Universal |
| M3 regression | ✅ | Universal |
| M4 lint | ✅ | TypeScript files in diff (schema + utility + tests) |
| M5 dead-code | ❌ | Additive change — no deletions in diff |
| S1 dataFlow | ✅ | Schema files in diff — sanitization changes data flow from input → DB |
| S2 auth | ❌ | No auth/route files in diff |
| S3 injection | ✅ | This IS the XSS defense — must verify no bypass vectors |
| P1 query | ❌ | No DB/repository query changes |
| P2 memory | ❌ | No collection/buffer changes |
| P3 latency | ❌ | No p95_target_ms in plan — sanitization is O(n) on string length, negligible |

## Observable Level

| Decision | Value |
|---|---|
| **O-Level** | O2 |
| **Max Capability** | O4 |
| **Browser Available?** | NO — not needed for this task |
| **Capped?** | O4 → O2 (no browser needed; O2 = verify via test execution) |
| **Fallback Strategy** | Run full test suite including new sanitization tests |
| **Residual Risk** | Low — sanitization is deterministic; risk is in edge-case bypasses that adversarial review should catch |

## Progressive Widening Policy

| Stage | Trigger Threshold | Max Lanes |
|---|---|---|
| Stage 1 | uncertainty_score < 30 | 3 |
| Stage 2 | 30 ≤ uncertainty < 60 | 7 |
| Stage 3 | uncertainty ≥ 60 | 10 |

## Escalation Rules

| Rule | Trigger | Action |
|---|---|---|
| No new evidence | 1 cycle with Δ=0 | Re-dispatch D1 (pro) → plan re-eval → user |
| Same gate ×2 | Same gate fails twice | ESCALATE to user |
| Budget near limit | 80% of max cycles | ESCALATE |
| Scope creep | D2 flags scope change | Return to planner |

## Failure-Pattern Feed

| Pattern ID | Gate | Symptom | Last Seen | Effectiveness | Action |
|---|---|---|---|---|---|
| _none_ | _none_ | _no prior failures in input sanitization area_ | _N/A_ | _N/A_ | _N/A_ |

## Loop ROI Estimate

| Metric | Estimate |
|---|---|
| **Tokens (discovery)** | ~6K |
| **Tokens (TDD + PDCA)** | ~10K |
| **Tokens (QA)** | ~5K |
| **Total estimated** | ~21K |
| **Est. cost (flash)** | ~$0.002 |
| **Est. cost (pro)** | ~$0.06 |
| **Est. cost (blended)** | ~$0.03 |
| **Historical ROI** | 0.92 (security-hardening task area — highest ROI category) |
| **Budget utilization** | 4% of STANDARD mode budget |
| **Recommendation** | PROCEED |

---

## Change Surface Analysis

### Files to create
| File | Purpose |
|---|---|
| `src/lib/sanitize.ts` | Sanitization utility function |
| `__tests__/lib/sanitize.test.ts` | Unit tests for sanitization |

### Files to modify
| File | Change |
|---|---|
| `src/schemas/task.schema.ts` | Add `.transform()` to `title` and `description` fields in `createTaskSchema` and `updateTaskSchema` |

### No change needed
- Controllers, services, repositories, routes, middleware — they pass Zod-parsed data through
- The `validate.ts` middleware calls `schema.parse()` which applies transforms automatically

## Architecture Decision

### Where sanitization lives

**Zod `.transform()` on schema fields** — NOT middleware, NOT service layer.

Rationale:
1. Zod transforms run during `schema.parse()` — the same validation pass that already exists
2. The `validateBody()` middleware already calls `schema.parse()` and stores the result — transforms are applied automatically
3. No new middleware needed — no risk of middleware ordering bugs
4. A separate `sanitizeText()` utility keeps the transform logic testable in isolation

### Sanitization pipeline order
1. **Trim** — remove leading/trailing whitespace first (makes subsequent checks accurate)
2. **Strip HTML tags** — regex `/<[^>]*>/g` removes all HTML tags
3. **HTML-escape** — escape `&`, `<`, `>`, `"`, `'` to entity references
4. **Preserve emoji** — emoji are Unicode characters, unaffected by any of the above operations

### Why HTML-escape AFTER tag stripping
If we escape first (`<` → `&lt;`), then the tag-stripping regex won't match anymore. The tag-stripping regex `/<[^>]*>/g` matches literal `<` and `>` characters, not entities. So we must strip tags first, then escape any remaining special characters (e.g., a bare `&` in user text that isn't part of an HTML entity).

Actually — re-examine: HTML-escaping `&` would break existing entities like `&amp;` into `&amp;amp;`. The correct approach:
1. Trim
2. Strip HTML tags (removes `<script>`, `<img onerror=...>`, etc.)
3. Escape `&`, `<`, `>`, `"`, `'` — but only the bare characters, not already-escaped entities

Simpler: after tag stripping, there are no HTML tags left. So escape the 5 special characters. The `&` escape must come FIRST in the replacement order to avoid double-escaping.

Sanitization order: Trim → Strip tags → Escape `&` → Escape `<` → Escape `>` → Escape `"` → Escape `'`

## Test Specifications

### Unit tests (`sanitize.test.ts`)
1. **Trim**: `"  hello  "` → `"hello"`
2. **HTML tag stripping**: `"<script>alert('xss')</script>"` → `"alert('xss')"`
3. **XSS prevention**: `"<img src=x onerror=alert(1)>"` → `"img src=x onerror=alert(1)"` → `"img src=x onerror=alert(1)"` (no < > to escape after strip, but wait — the tag regex strips the whole thing including content? No: `<img src=x onerror=alert(1)>` — the regex `/<[^>]*>/g` matches the whole tag including attributes. The content inside `alert(1)` is inside the attribute quote, which is inside the `<>`, so the whole thing is stripped. Result: `""`. Let's reconsider — actually the regex `/<[^>]*>/g` matches `<img src=x onerror=alert(1)>` as one match, so it's all removed.
   
   Better test: `"Hello <b>world</b>"` → `"Hello world"` (tags stripped, text preserved)
4. **Emoji preservation**: `"Hello 🎉 world 🌍"` → `"Hello 🎉 world 🌍"` (unchanged)
5. **Combined**: `"  <script>alert('xss')</script> 🎉  "` → `"alert('xss') 🎉"` (trim + strip + emoji)
6. **Ampersand escaping**: `"A & B"` → `"A &amp; B"` (after tag strip, no tags → escape &)
7. **Quote escaping**: `"say \"hello\""` → `"say &quot;hello&quot;"`
8. **Empty/null/undefined**: `""` → `""`, `null` → `null`, `undefined` → `undefined`
9. **No tags, no special chars**: `"Plain text"` → `"Plain text"` (identity)
10. **Only emoji**: `"🎉🌟💯"` → `"🎉🌟💯"` (identity)
11. **Nested tags**: `"<div><p>text</p></div>"` → `"text"`
12. **XSS event handler**: `"<div onmouseover=\"alert(1)\">hover</div>"` → `"hover"`

### Integration tests (in routes test)
- POST with XSS payload → stored sanitized, response sanitized
- PUT with XSS payload → stored sanitized
- GET returns sanitized content

## Post-Governance Self-Audit

After pipeline completes, verify:
- [ ] `src/lib/sanitize.ts` exists with `sanitizeText()` function
- [ ] `createTaskSchema.title` has `.transform(sanitizeText)`
- [ ] `createTaskSchema.description` has `.transform(sanitizeText)`
- [ ] `updateTaskSchema.title` has `.transform(sanitizeText)` for optional field
- [ ] `updateTaskSchema.description` has `.transform(sanitizeText)` for optional field
- [ ] All existing tests pass (regression)
- [ ] New sanitize unit tests pass
- [ ] Emoji preserved through sanitization
- [ ] XSS vectors neutralized
- [ ] HTML tags stripped
- [ ] Whitespace trimmed
