# Plan: Add --verbose to blackcow-librarian check

| Field | Value |
|---|---|
| **Slug** | `librarian-check-verbose` |
| **Created** | 2026-06-20 |
| **Class** | XS |
| **Explore lanes** | 5 dispatched, 4 timeout+retry, 1 returned + file content from initial read |
| **Adversarial reviews** | N/A (XS skip) |
| **Budget** | ~3K tokens / 115K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | `check` 명령어가 캐시 전체 크기만 보여주고 개별 파일 크기를 보여주지 않아, 어떤 캐시 파일이 가장 큰지/비대해졌는지 진단 불가 |
| **WHO** | blackcow-librarian 사용자 및 downstream skills (plan/loop/qa) 운영자 |
| **WHAT** | `--verbose` 플래그 추가 시 check 출력에 캐시 파일별 크기 표시 |
| **RISK** | 없음 — 기존 출력 포맷에 추가만 하므로 하위 호환성 유지. 기존 consumers (plan/loop/qa Phase 0 cache load)는 check-result.txt의 key:value 라인만 파싱하므로 영향 없음 |
| **SUCCESS** | (1) `--command=check --verbose` → 파일별 크기 표시, (2) `--command=check` (플래그 없음) → 기존 출력과 완전히 동일, (3) check-result.txt에 verbose 시 파일 크기 포함 |
| **SCOPE** | `skills/blackcow-librarian.md` Phase 5 (check) 섹션 (line ~515-570). Phase 0 입력 설명 1줄 추가. 그 외 섹션 변경 없음 |

## Summary

`blackcow-librarian check` 명령어에 `--verbose` 플래그를 추가한다. verbose 모드에서는 기존 캐시 상태 테이블 아래에 **Cache File Sizes** 하위 테이블을 추가로 출력하고, evidence 파일(`check-result.txt`)에도 파일별 크기를 포함한다. 플래그 미지정 시 기존 출력과 100% 동일하게 유지하여 downstream consumers(plan/loop/qa의 Phase 0 cache load)에 영향을 주지 않는다.

## Codebase Survey

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| Surface | check는 Phase 5, 515-570라인. 입력 파싱은 43라인 `arguments` 설명 | read_file full | — |
| Call Graph | check 호출자: load(Phase 6.1)에서 inline 호출, plan/loop/qa의 Phase 0.0 Cache Load에서 check-result.txt 읽음 | search_content | — |
| Data Shapes | check 입력: `--command=check`, `--model-tier=`. check 출력: 마크다운 테이블(5.2) + check-result.txt(5.3). cache artifacts: head.sha256, scanned-at.txt, structure-cache.jsonl, dep-graph.json, entry-exit.json, dir-scores.json | read_file full | S1 |
| Patterns | L1_PROMPT(Library State)에서 이미 `wc -c`로 파일 크기 수집 패턴 존재 (line ~92-96). 프로젝트 전체에 `--verbose`/`--debug` 플래그 선례 없음 — 신규 패턴 | search_content: no matches | — |
| Artifacts | check-result.txt 실존: `Verdict: EMPTY` (캐시 없음). meta-review에서 `.omo/library/` 미생성 지적 (10+ 사이클) | explore L5 + read_file | M2 |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🔧 Modify | `## Input` 섹션: `arguments` 설명에 `--verbose` 추가 | `skills/blackcow-librarian.md:43` | HIGH | low | M1 |
| 🔧 Modify | Phase 5.1: verbose 시 파일별 크기 수집 로직 추가 | `skills/blackcow-librarian.md:520-536` | HIGH | low | M1 |
| 🔧 Modify | Phase 5.2: verbose 전용 Cache File Sizes 테이블 추가 | `skills/blackcow-librarian.md:538-558` | HIGH | low | M1 |
| 🔧 Modify | Phase 5.3: check-result.txt에 verbose 시 파일 크기 포함 | `skills/blackcow-librarian.md:560-570` | HIGH | low | M5 |
| ✅ Reuse | L1_PROMPT의 `wc -c` 파일 크기 수집 패턴 (line 92-96) | `skills/blackcow-librarian.md:92-96` | HIGH | — | — |

## Waves

### Wave 1 — Verbose Flag (4 tasks, serial-safe, ~2K tokens)

- [ ] **mod-1**: `## Input` 섹션 (line 43) — arguments 설명에 `--verbose` 추가
  - **Worker:** mini
  - **Token est:** ~0.3K
  - **Verify:** `grep -n '\-\-verbose' skills/blackcow-librarian.md | head -5`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/ulw-loop/evidence/librarian-check-verbose-w1-mod1.txt`

- [ ] **mod-2**: Phase 5.1 (line ~520-536) — Freshness Check Logic에 verbose 분기 추가
  - **Worker:** medium
  - **Token est:** ~0.8K
  - **Verify:** `grep -A5 'verbose' skills/blackcow-librarian.md | grep -E 'wc -c|file.*size|KB'`
  - **Gate:** M1 (spec-match), M5 (dead-code)
  - **Evidence:** `.omo/ulw-loop/evidence/librarian-check-verbose-w1-mod2.txt`

- [ ] **mod-3**: Phase 5.2 (line ~538-558) — Check Output에 verbose 전용 Cache File Sizes 하위 섹션 추가
  - **Worker:** medium
  - **Token est:** ~0.6K
  - **Verify:** `grep -A15 'Cache File Sizes' skills/blackcow-librarian.md`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/ulw-loop/evidence/librarian-check-verbose-w1-mod3.txt`

- [ ] **mod-4**: Phase 5.3 (line ~560-570) — check Evidence에 verbose 시 파일별 크기 추가
  - **Worker:** mini
  - **Token est:** ~0.3K
  - **Verify:** `grep -A5 'Cache Files' .omo/ulw-loop/evidence/check-result.txt 2>/dev/null || echo "Evidence format verified in skill definition"`
  - **Gate:** M5 (dead-code — ensure no orphaned fields)
  - **Evidence:** `.omo/ulw-loop/evidence/librarian-check-verbose-w1-mod4.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| 기존 출력 파괴 | `M1_spec_match` | HIGH | matchRate ≥ 90% | verbose 미지정 시 5.2/5.3 출력 완전히 동일하게 유지 | `diff <(before) <(after)` — 기존 필드 변화 없음 |
| Downstream 파싱 깨짐 | `M3_regression` | MED | 0 regressions | check-result.txt는 기존 key:value 라인을 그대로 유지하고 verbose 라인만 추가 | grep으로 기존 키(`Verdict:`, `HEAD Match:`, `Days Stale:`, `Integrity:`) 존재 확인 |
| Dead code | `M5_dead_code` | LOW | 0 unused exports | verbose 분기 내 모든 수집 필드는 5.2/5.3에서 소비됨 | grep으로 각 수집 변수가 출력 섹션에서 참조되는지 확인 |

## Execution Command
```
blackcow-loop "Execute plans/librarian-check-verbose.md" --completion-promise='--command=check --verbose prints per-file cache sizes; --command=check (no flag) output is unchanged; check-result.txt unchanged without verbose' --trust-level=2
```

### Parallelism Guide
- Wave 1: 4 modifications all within Phase 5 section of one file — can be done sequentially or in 2 parallel pairs (mod-1+mod-4 parallel, mod-2+mod-3 parallel)
- Total budget: ~2K / 115K target

---

## Detailed Implementation Spec

### mod-1: Input section — add `--verbose` to argument description

**Current (line 43):**
```
`arguments`: `--command=<name>` (required, one of: init-deep, scan, update, check, load), plus optional target directory path.
```

**Change to:**
```
`arguments`: `--command=<name>` (required, one of: init-deep, scan, update, check, load), plus optional `--verbose` flag and target directory path. `--verbose` enables per-file cache size breakdown on `check` command output.
```

### mod-2: Phase 5.1 — add verbose file size collection

**Insert after step 6 (integrity check) in 5.1:**

```
7. If --verbose: collect per-file sizes for all cache artifacts:
   - structure-cache.jsonl: <N> KB
   - dep-graph.json: <N> KB
   - entry-exit.json: <N> KB
   - dir-scores.json: <N> KB
   - head.sha256: <N> bytes
   - scanned-at.txt: <N> bytes
   - Total: <N> KB
```

### mod-3: Phase 5.2 — add verbose output section

**Insert after the main check output table, before the 5.3 heading:**

```markdown
### 5.2b Verbose Output (only when --verbose)

When `--verbose` is set, append the following after the main status table:

```markdown
### Cache File Sizes
| File | Size |
|---|---|
| `structure-cache.jsonl` | <N> KB |
| `dep-graph.json` | <N> KB |
| `entry-exit.json` | <N> KB |
| `dir-scores.json` | <N> KB |
| `head.sha256` | <N> bytes |
| `scanned-at.txt` | <N> bytes |
| **Total** | **<N> KB** |
```
```

### mod-4: Phase 5.3 — add verbose evidence

**Current 5.3 format:**
```
# check Result
Timestamp: <ISO>
Verdict: FRESH|STALE|EMPTY|NO_GIT
HEAD Match: yes|no|N/A
Days Stale: <N>
Integrity: valid|corrupt
```

**Change to (add conditional block):**
```
# check Result
Timestamp: <ISO>
Verdict: FRESH|STALE|EMPTY|NO_GIT
HEAD Match: yes|no|N/A
Days Stale: <N>
Integrity: valid|corrupt
[if --verbose:]
Cache Files:
  structure-cache.jsonl: <N> KB
  dep-graph.json: <N> KB
  entry-exit.json: <N> KB
  dir-scores.json: <N> KB
  head.sha256: <N> bytes
  scanned-at.txt: <N> bytes
  TOTAL: <N> KB
```
