# Plan: Markdown API Reference Documentation Generator

| Field | Value |
|---|---|
| **Slug** | `sim-markdown-docs` |
| **Created** | 2026-06-27T23:00:00Z |
| **Class** | M |
| **Explore lanes** | 2 dispatched, 2 returned |
| **Adversarial reviews** | 1/1 passed, 24 findings incorporated |
| **Budget** | estimated 45K tokens / 115K target |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | TypeScript 프로젝트에서 JSDoc 주석이 작성되어 있으나, 이를 읽기 쉬운 Markdown API 문서로 자동 변환하는 경량 도구가 부재함. TypeDoc은 무겁고 출력 커스터마이징이 제한적임. |
| **WHO** | TypeScript 라이브러리/패키지 메인테이너, 오픈소스 기여자, API 문서화가 필요한 개발팀 |
| **WHAT** | `api-doc-gen` CLI 도구 — TypeScript 소스 파일을 glob으로 찾고, AST에서 JSDoc 추출 후, Handlebars 템플릿으로 Markdown 문서 생성 |
| **RISK** | 실패 시 수동 문서화 부담 지속. 최대 허용 다운타임: N/A (개발 도구, runtime 의존성 없음) |
| **SUCCESS** | matchRate ≥ 90% (5개 핵심 요구사항 + 24개 adversarial edge cases 충족), test pass=100%, lint=0warn, coverage ≥ 80%, p95_target_ms: <500ms per 100 files |
| **SCOPE** | 포함: TypeScript 파일 glob 검색, JSDoc AST 추출 (25+ tags), Markdown 렌더링, CLI 인터페이스, 템플릿 커스터마이징, cross-reference resolution (two-pass). 제외: 실시간 watch 모드 (v2), PDF/HTML 출력, 웹 UI, npm 배포 자동화 |

## Summary

Greenfield CLI tool that reads TypeScript source files via glob patterns, traverses their AST using the TypeScript Compiler API to extract JSDoc comments into a structured intermediate model, then renders that model through Handlebars templates into Markdown documentation. A two-pass architecture (collect → resolve) handles cross-references and `{@link}` tags correctly. The pipeline is: **glob discovery → AST parse → JSDoc extraction → Comment model → two-pass link resolution → Handlebars rendering → .md output**.

## Architecture Options

### Option A — Minimal: TypeDoc Wrapper
- **접근법**: TypeDoc을 dependency로 사용, `typedoc --plugin typedoc-plugin-markdown` 구성, 필요 시 plugin으로 커스텀 확장
- **장점**: 구현 비용 최소 (설정 파일 + plugin 1개), TypeDoc의 검증된 JSDoc 파서 재사용
- **단점**: TypeDoc 버전에 종속, 템플릿 커스터마이징이 plugin API로 제한됨, CLI 플래그가 TypeDoc 컨벤션에 묶임
- **적합**: 빠른 PoC, TypeDoc 생태계에 이미 투자한 팀
- **예상 파일 수**: 3-5개 (설정 + plugin + 테스트)

### Option B — Clean: Full Custom Pipeline
- **접근법**: TS Compiler API로 AST 직접 순회, 자체 JSDoc lexer/parser 구현, Handlebars 템플릿 엔진, 완전한 CLI 프레임워크 (commander/yargs), 설정 파일 파서, watch 모드, 플러그인 시스템
- **장점**: 완전한 제어, 어떤 출력 형식이든 지원 가능, 의존성 최소화
- **단점**: 개발 비용 높음 (~2-3주), JSDoc 스펙 전체 구현 부담, 자체 버그 표면적 큼
- **적합**: 장기 유지보수가 예상되는 독립 제품
- **예상 파일 수**: 20-30개

### Option C — Pragmatic: TS API + Handlebars (권장)
- **접근법**: TS Compiler API로 AST 순회 (thin wrapper), JSDoc 태그 추출은 TS 내장 API 활용 (`ts.getJSDocCommentsAndTags`), Handlebars 템플릿 엔진, 경량 CLI (parseArgs), 설정 파일 지원. Two-pass linker: Pass 1 collects all entity names+anchors → symbol table; Pass 2 resolves every `{@link}` / `@see` by lookup.
- **장점**: 의존성 3개 이하 (typescript, handlebars, glob). TS API의 JSDoc 지원 활용으로 파서 재구현 불필요. 템플릿 교체로 출력 형식 완전 제어 가능
- **단점**: TS API의 JSDoc 표현이 저수준이라 Comment 모델로 변환하는 추상화 레이어 필요. Handlebars 헬퍼 등록 패턴 학습 필요
- **적합**: 대부분의 실제 사용 사례. 개발 비용과 유연성의 균형
- **예상 파일 수**: 10-14개

### 권장: Option C (Pragmatic)
**사유**: Lane 1 조사 결과 TS Compiler API 자체가 JSDoc 주석을 구조화된 형태로 제공하므로(`ts.getJSDocCommentsAndTags`), 자체 lexer/parser를 작성할 필요가 없음. Lane 2 조사 결과 Handlebars가 TypeScript 문서화 도구에서 검증된 패턴이며(TypeDoc도 Handlebars 기반), 부분 템플릿(partials)이 entity type(class/function/enum)과 1:1 매핑되어 직관적임. Option B의 자체 JSDoc 파서는 과잉 설계.

## Codebase Survey (2-Lane Summary)

| Lane | Key Finding | Evidence | BKIT Gate |
|---|---|---|---|
| **L1 — Parsing Pipeline** | TS Compiler API (`ts.createSourceFile`, `ts.getJSDocCommentsAndTags`, `ts.forEachChild`)만으로 전체 JSDoc 추출 가능. ts-morph, babel 불필요. | Lane 1 — TS API surface survey | S1 |
| **L1 — Type Serialization** | 복합 타입 직렬화는 `ts.TypeChecker.typeToString(type)`를 1차로 사용, 실패 시 `node.getText()`로 fallback. Mapped types, template literal types, conditional types 모두 처리 가능. | Lane 1 — `resolveTypeString()` 연구 | M1 |
| **L1 — JSDoc Tags** | 25+ 태그 카탈로그: `@param`, `@returns`, `@throws`, `@example`, `@deprecated`, `@see`, `@since`, `@template`, `@overload`, `@type`, `@default`, `@remarks`, `@beta`, `@alpha`, `@internal`, `@category`, `@enum`, `@implements`, `@interface`, `@namespace`, `@property`, `@typedef`, `@callback`, `@link`, `@linkcode`, `@linkplain` | Lane 1 — JSDoc spec + TypeDoc source 분석 | M1 |
| **L1 — TypeScript Constructs** | Generics `<T extends X>`, union `A \| B`, intersection `A & B`, conditional `T extends U ? X : Y`, type aliases, interfaces, enums, `export default`, `declare`, namespace, abstract class, optional `?`, `readonly`, index signatures, mapped types, template literal types, import types — 모두 처리 | Lane 1 + adversarial review | M1 |
| **L2 — Output Pipeline** | Handlebars 권장: partials가 entity type과 1:1 매핑. `{{> class}}`, `{{> function}}`, `{{> enum}}`, `{{> typeAlias}}`. 커스텀 헬퍼: `{{#code}}`, `{{#link}}`, `{{#heading}}`, `{{#table}}`, `{{#anchor}}` | Lane 2 — rendering strategy comparison | S1 |
| **L2 — Two-Pass Linker** | Pass 1: 모든 entity name+anchor를 symbol table에 수집. Pass 2: `{@link}`, `@see`, import type 참조를 모두 resolve. Unresolved → warning 출력 | Adversarial review — finding #3/#6/#17 | M1 |
| **L2 — Heading Hierarchy** | `h1`: Module, `h2`: Section (Exports/Types/Functions), `h3`: Entity name, `h4`: Constructor/Method/Property section, `h5`: Individual parameter/property | Lane 2 — Markdown structure design | M1 |
| **L2 — CLI Design** | `--input` (glob), `--output` (dir), `--template` (path), `--format` (single/multi/hybrid), `--toc`, `--include/--exclude`, `--heading-offset`, `--ambient`, `--verbose`. Exit codes: 0=success, 1=parse error, 2=template error, 3=config error, 4=internal | Lane 2 + adversarial review (#11) | M1 |
| **L2 — File Organization** | Hybrid default: `docs/api/index.md` + `modules/*.md` + (optional) `entities/*.md`. Anchor links: module-qualified to prevent conflicts (`#src-types-task-Task` not just `#Task`). | Lane 2 + adversarial review (#18) | M1 |

## Gap Matrix

| Cat | Item | Evidence | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | `src/types.ts` — Core TypeScript types: `Comment`, `Tag`, `Entity`, `Module`, `Config`, `CliOptions`, `SymbolTable`, `AnchorMap` | Both lanes | — | — | S1 |
| 🆕 Build | `src/discovery.ts` — Glob-based file discovery with include/exclude filters, `tsconfig.json` resolution for module paths | Lane 2 | — | — | M1 |
| 🆕 Build | `src/model.ts` — Comment/Tag/Entity data model with JSDoc tag catalog constants. Includes: `indexSignatures[]`, `isAbstract`, `isDeclare`, `overloads[]` | Both lanes + review | — | — | S1 |
| 🆕 Build | `src/parser.ts` — AST traversal: `createSourceFile`, `forEachChild`, `getJSDocCommentsAndTags`, `typeChecker.typeToString()`. Handles: overloads, re-exports, anonymous defaults, empty JSDoc skip, dot-separated param nesting, `@example` verbatim preservation | Lane 1 + review (#1,#4,#5,#8,#9,#10,#12,#13) | — | — | M1 |
| 🆕 Build | `src/linker.ts` — Two-pass cross-reference resolver: Pass 1 collects all `AnchorMap`, Pass 2 resolves `{@link}`, `@see` (URL vs symbol), import types. Unresolved → warning. Circular ref detection with depth cap. | Lane 2 + review (#3,#6,#17,#19) | — | — | M1 |
| 🆕 Build | `src/renderer.ts` — Handlebars engine wrapper: load templates (built-in or custom), register helpers (`#code`, `#link`, `#heading`, `#table`, `#anchor`), compile, invoke. `{{{ }}}` for verbatim content (examples). `{{ }}` with HTML-escaping for all other fields. | Lane 2 + review (#4,#7,#20,#22) | — | — | M1 |
| 🆕 Build | `templates/` — 12 Handlebars files: `module.hbs`, `class.hbs`, `function.hbs`, `enum.hbs`, `typeAlias.hbs`, `index.hbs`, `_params.hbs`, `_returns.hbs`, `_throws.hbs`, `_examples.hbs`, `_seeAlso.hbs`, `_toc.hbs` | Lane 2 | — | — | M1 |
| 🆕 Build | `src/cli.ts` — CLI entry point: flag parsing, config file loading (`.docsrc.json`, `typedoc.json` merge), pipeline wiring, exit codes | Lane 2 | — | — | M1 |
| 🆕 Build | `src/config.ts` — Config schema validation, auto-detect, CLI flag merge (CLI takes precedence). Handles missing/invalid JSON gracefully. | Lane 2 + review (#23,#24) | — | — | M1 |
| 🆕 Build | `tests/` — Unit tests (parser, linker, renderer, config, discovery), integration tests (real .ts files → .md output), snapshot tests (type serialization 15+ fixtures) | Both lanes | — | — | M2 |

## Waves

### Wave 1 — Foundation (4 tasks, ≤50K tokens)

- [ ] **w1-types**: Define core TypeScript types: `Comment`, `Tag`, `Entity` (with `indexSignatures`, `isAbstract`, `isDeclare`, `overloads`), `Module`, `Config`, `CliOptions`, `SymbolTable`, `AnchorMap`
  - **Worker:** mini
  - **Token est:** ~3K
  - **Files:** `src/types.ts`
  - **Verify:** `npx tsc --noEmit`
  - **Gate:** S1 (dataFlow)
  - **Evidence:** `.omo/evidence/w1-types.txt`

- [ ] **w1-model**: Implement Comment/Tag/Entity data model: JSDoc tag catalog constants (25+ tags), `@param` dot-path nesting into tree, `@overload` grouping by function name, empty JSDoc guard
  - **Worker:** medium
  - **Token est:** ~10K
  - **Files:** `src/model.ts`
  - **Verify:** `npx jest --testPathPattern=model --passWithNoTests`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/w1-model.txt`

- [ ] **w1-discovery**: Implement glob-based file discovery: read config, expand globs, filter include/exclude, resolve to absolute paths, find `tsconfig.json` for module resolution, handle "no matches" with warning
  - **Worker:** medium
  - **Token est:** ~8K
  - **Files:** `src/discovery.ts`
  - **Verify:** `npx jest --testPathPattern=discovery --passWithNoTests`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/w1-discovery.txt`

- [ ] **w1-config**: Implement config file support: auto-detect `.docsrc.json` and `typedoc.json`, merge with CLI flags (CLI takes precedence), validate config schema, graceful error on invalid JSON
  - **Worker:** medium
  - **Token est:** ~7K
  - **Files:** `src/config.ts`
  - **Verify:** `npx jest --testPathPattern=config --passWithNoTests`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/w1-config.txt`

### Wave 2 — Core Parsing (2 tasks, ≤60K tokens)

- [ ] **w2-parser**: Implement AST traversal using TS Compiler API
  - **Worker:** heavy
  - **Token est:** ~25K
  - **Files:** `src/parser.ts`
  - **Details:**
    - `createSourceFile` → `forEachChild` → `canHaveJSDoc` → `getJSDocCommentsAndTags`
    - Type serialization: `typeChecker.typeToString()` primary, `node.getText()` fallback, depth cap 5
    - Handle: overloads (group by name, render all signatures), re-exports (`export { Foo as Bar }` → redirect note), anonymous defaults (generate `_default` anchor), `declare`/`abstract` modifiers, index signatures, mapped types, template literal types, import types
    - `@param` dot-path → nested tree structure
    - `@example` → stored verbatim (preserve whitespace + code fences)
    - `@default` → stored as string, flagged for inline-code rendering
    - Empty `/** */` → skip entity entirely
    - `@internal` → excluded by default (configurable)
  - **Verify:** `npx jest --testPathPattern=parser --passWithNoTests`
  - **Gate:** M1 (spec-match), S1 (dataFlow)
  - **Evidence:** `.omo/evidence/w2-parser.txt`

- [ ] **w2-linker**: Implement two-pass cross-reference resolver
  - **Worker:** heavy
  - **Token est:** ~18K
  - **Files:** `src/linker.ts`
  - **Details:**
    - Pass 1: Walk all entities → build `AnchorMap` (entity name → module-qualified anchor `#src-types-task-Task`)
    - Pass 2: For every entity, resolve `{@link}` / `{@linkcode}` / `{@linkplain}` inline tags, `@see` tags (URL detection: starts with `http` → external link; else → symbol lookup), import types (`import('./foo').Bar` → relative link)
    - Circular reference detection: Set-based cycle guard, max depth 5
    - Unresolved references → emit warning to stderr, render as plain text in output
    - Anchor conflict prevention: module-qualified anchors (`#modulepath-entityname`)
  - **Verify:** `npx jest --testPathPattern=linker --passWithNoTests`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/w2-linker.txt`

### Wave 3 — Output Pipeline (2 tasks, ≤45K tokens)

- [ ] **w3-templates**: Create built-in Handlebars templates
  - **Worker:** medium
  - **Token est:** ~12K
  - **Files:** `templates/module.hbs`, `templates/class.hbs`, `templates/function.hbs`, `templates/enum.hbs`, `templates/typeAlias.hbs`, `templates/index.hbs`, `templates/_params.hbs`, `templates/_returns.hbs`, `templates/_throws.hbs`, `templates/_examples.hbs`, `templates/_seeAlso.hbs`, `templates/_toc.hbs`
  - **Details:**
    - Module template: `# ModuleName` → `## Exports` → each entity via `{{> entityType}}`
    - Class template: `### ClassName` with `**Abstract**` badge conditionally, `#### Constructor`, `#### Methods`, `#### Properties`
    - Function template: `### functionName` with overload handling (multiple `#### Overload N` sub-sections)
    - Enum template: `### EnumName` with member table
    - `_params.hbs`: parameter table with dot-path nesting (`options.foo` → indented sub-row)
    - `_examples.hbs`: `{{{exampleBody}}}` (triple-stash for verbatim)
    - `_seeAlso.hbs`: resolved vs unresolved link rendering
    - `_toc.hbs`: auto-generated from heading hierarchy
    - Long type signatures (>200 chars): wrap in `<details>` block or code block with horizontal scroll
    - Entities with no JSDoc: render signature only, no description section
  - **Verify:** `node -e "const H = require('handlebars'); const fs = require('fs'); ['module','class','function','enum','typeAlias','index'].forEach(f => H.compile(fs.readFileSync('templates/'+f+'.hbs','utf8'))); console.log('OK')"`
  - **Gate:** M1 (spec-match)
  - **Evidence:** `.omo/evidence/w3-templates.txt`

- [ ] **w3-renderer**: Implement Handlebars renderer wrapper
  - **Worker:** heavy
  - **Token est:** ~18K
  - **Files:** `src/renderer.ts`
  - **Details:**
    - Load templates: built-in default or custom `--template` directory (missing partials → fallback to built-in)
    - Register helpers: `{{#code}}` (inline code), `{{#codeBlock}}` (fenced block), `{{#link target}}` (resolved cross-ref), `{{#heading level}}` (with auto-anchor), `{{#table headers rows}}`, `{{#anchor name}}` (GitHub-flavored)
    - Output organization: `--format=single` → `{output}/modules/{module}.md`, `--format=multi` → `{output}/entities/{entity}.md`, `--format=hybrid` → `index.md` + both
    - `--heading-offset=N`: shift all heading levels by +N
    - `--toc`: conditionally prepend `_toc.hbs` to each file
    - Handlebars `{{ }}` escaping in code: use `\{{ }}` or raw block helper for template-literal-type examples
  - **Verify:** `npx jest --testPathPattern=renderer --passWithNoTests`
  - **Gate:** M1 (spec-match), S1 (dataFlow)
  - **Evidence:** `.omo/evidence/w3-renderer.txt`

### Wave 4 — Integration + CLI (3 tasks, ≤35K tokens)

- [ ] **w4-cli**: Implement CLI entry point
  - **Worker:** heavy
  - **Token est:** ~15K
  - **Files:** `src/cli.ts`, `bin/api-doc-gen`
  - **Details:**
    - Flag parsing (`parseArgs` or `mri`): `--input`, `--output`, `--template`, `--format`, `--toc`, `--include`, `--exclude`, `--heading-offset`, `--ambient`, `--verbose`
    - Config auto-detection: `.docsrc.json` → `typedoc.json` → CLI flags (CLI wins)
    - Pipeline wiring: discovery → parser → linker → renderer
    - Exit codes: 0=success, 1=parse error (TS syntax), 2=template error (missing partial/syntax), 3=config error (invalid flag combo, missing input), 4=internal (unhandled exception)
    - `--help` auto-generated from flag schema
    - Glob injection guard: reject patterns with `..` path traversal
  - **Verify:** `npx jest --testPathPattern=cli --passWithNoTests`
  - **Gate:** M1 (spec-match), S3 (injection)
  - **Evidence:** `.omo/evidence/w4-cli.txt`

- [ ] **w4-integration**: Integration tests + snapshot tests
  - **Worker:** medium
  - **Token est:** ~10K
  - **Files:** `tests/integration.test.ts`, `tests/__snapshots__/`, `tests/fixtures/`
  - **Details:**
    - Feed real `.ts` files (use `src/types/*.ts` from this project as fixtures)
    - Verify Markdown output: heading hierarchy, anchor links, cross-references
    - Snapshot tests: 15+ TypeScript type fixtures (generics, unions, intersections, conditional, mapped, template literal, import types)
    - Error scenario tests: invalid TS syntax → exit 1, missing template → exit 2, invalid config → exit 3
    - End-to-end: parse → link → render → compare Markdown output to golden file
    - Performance benchmark: 100 files × 10 entities → <500ms
  - **Verify:** `npm test -- --coverage`
  - **Gate:** M2 (test pass=100%)
  - **Evidence:** `.omo/evidence/w4-integration.txt`

- [ ] **w4-coverage**: Final quality gate check
  - **Worker:** mini
  - **Token est:** ~2K
  - **Files:** (none — verification only)
  - **Details:**
    - `npm run lint` → 0 warnings
    - `npm test -- --coverage` → ≥80% coverage
    - `npm run typecheck` → 0 errors
    - JSDoc tag count: ≥25 tags have unit tests
  - **Verify:** `npm run lint && npm test -- --coverage && npm run typecheck`
  - **Gate:** M4 (lint clean), M2 (coverage)
  - **Evidence:** `.omo/evidence/w4-coverage.txt`

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| JSDoc tag parsing incomplete | `M1_spec_match` | HIGH | ≥25 tags supported | Tag catalog as test checklist; each tag has dedicated unit test | `grep -c 'it(' tests/parser.test.ts` ≥ 25 |
| TypeScript type serialization incorrect | `M1_spec_match` | HIGH | All constructs rendered correctly | `typeChecker.typeToString()` primary + `node.getText()` fallback + depth cap 5. Snapshot tests for 15+ type fixtures | Snapshot diff = 0 |
| Anchor conflicts between same-named entities in different files | `M1_spec_match` | HIGH | 0 conflicts | Module-qualified anchors: `#src-types-task-Task` not `#Task`. AnchorMap keyed by fully-qualified path | `grep -c 'UNRESOLVED' output/*.md` = 0 |
| `@overload` signatures dropped or merged incorrectly | `M1_spec_match` | HIGH | All overloads rendered | Group by function name; each overload rendered as sub-heading under shared entity heading | Snapshot test: 3-overload function → 3 sub-sections |
| Data model mismatch between parser and renderer | `S1_dataFlow` | HIGH | integrity ≥ 90% | Typed interface contract (`src/types.ts`); integration test validates end-to-end | E2E test: parse → render → compare |
| Two-pass linker: pass 1 entities missing when pass 2 resolves | `M1_spec_match` | MED | 0 unresolved links from valid targets | Strict ordering: all entities collected before any resolution. Symbol table built first. | `grep 'UNRESOLVED' output/*.md` = 0 |
| `@example` verbatim corruption (code fences, whitespace) | `M1_spec_match` | MED | Examples preserved exactly | Store `@example` content verbatim; render with `{{{ }}}` (triple-stash, no escaping). Gate on `@example` tag specifically — not all tags. | Snapshot: multiline example with ` ```ts ` fences → output matches |
| Handlebars `{{ }}` conflicts with template literal types in code | `M1_spec_match` | MED | 0 rendering artifacts | Raw block helper or `\{{ }}` escaping for code blocks containing Handlebars-like syntax | Grep output for stray `[object Object]` → 0 |
| Circular type references → infinite recursion | `S1_dataFlow` | MED | 0 infinite loops | Cycle detection with Set-based guard; max depth 5 in type serialization | Test: self-referencing type `type Node = { children: Node[] }` → rendered within depth limit |
| Template syntax errors at runtime | `M2_test_pass` | MED | passRate = 100% | Handlebars precompilation check in CI; template validation on startup | `node -e "Handlebars.precompile(fs.readFileSync(...))"` for each .hbs |
| Anonymous default export — no name for anchor | `M1_spec_match` | LOW | Generated anchor falls back correctly | Fallback: `module-slug_default` anchor; heading rendered as `default` | Test: `export default function() {}` → heading + anchor generated |
| `@see` URL vs symbol ambiguity | `M1_spec_match` | LOW | Correct link type rendered | URL prefix detection (`http://` / `https://`) → external link; else → symbol table lookup | Snapshot: `@see https://example.com` → `<a href>`; `@see MyClass` → `[MyClass](#...)` |
| Re-exports (`export { Foo as Bar }`) — docs for Bar missing | `M1_spec_match` | LOW | Re-exported symbols documented | Same-project: redirect note "Re-exported as **Bar**" linking to source. External: inline imported docs or "Re-exported from external." | Test: `export { TaskStatus as Status }` → Status section with redirect link |
| Glob pattern injection via user input | `S3_injection` | LOW | No filesystem escape | Validate patterns: reject `..` path traversal; resolve to absolute paths; audit before include | `echo '../etc/passwd'` → rejected with config error |
| Large codebase performance | `P3_latency` | LOW | p95 < 500ms per 100 files | Single-pass AST traversal; no re-parsing; lazy comment extraction (skip nodes without `canHaveJSDoc`) | Benchmark: 100 files × 10 entities → <500ms |
| TypeScript syntax errors in input files | `M3_regression` | LOW | Clear error message, continue | Catch `ts.SyntaxError`; report file:line:message; continue with remaining files; exit 1 if any errors | `api-doc-gen --input='src/broken.ts'` → exit 1 + stderr message |
| Empty JSDoc `/** */` causes crash | `M1_spec_match` | LOW | Skip gracefully | `if (jsDoc.tags?.length === 0 && !jsDoc.comment)` → skip entity | Test: `/** */ class Foo {}` → skipped, no output |
| Config file with invalid JSON | `M1_spec_match` | LOW | Graceful error, exit 3 | `JSON.parse` in try/catch; report parse error with file path + line info | Test: invalid `.docsrc.json` → exit 3 + message |
| `@internal` entities leaked into public docs | `M1_spec_match` | LOW | Excluded by default | Filter: `@internal` tag → skip entity. Configurable via `--include=internal` | Test: `/** @internal */ export function foo()` → absent from output |

## Execution

Run this plan with:
```
blackcow-loop "Execute plans/sim-markdown-docs.md" --completion-promise='All 4 waves complete: (1) CLI generates valid Markdown from TypeScript+JSDoc input, (2) 25+ JSDoc tags supported, (3) cross-references resolved correctly, (4) test pass=100%/coverage≥80%/lint=0warn' --trust-level=2
```

### Parallelism Guide

```
Wave 1: 4 tasks parallel (types → model | discovery | config after types)
  Critical: w1-types must complete before w1-model and w1-discovery
  
Wave 2: 2 tasks parallel (parser || linker)
  Critical: both depend on Wave 1 completion
  parser depends on: w1-model, w1-discovery
  linker depends on: w1-model

Wave 3: serial (templates → renderer)
  templates depends on: w2-parser (needs entity model shape)
  renderer depends on: w3-templates, w2-linker

Wave 4: 2 tasks parallel (cli || integration)
  cli depends on: w3-renderer, w1-discovery
  integration depends on: w4-cli (serial — needs CLI binary)
  config already done in Wave 1

Total: ~190K tokens estimated / 115K effective budget
  → Split into Foundation Plan (Waves 1-2, ~110K) + Integration Plan (Waves 3-4, ~80K)
  → Or run with --max-context=200K if model supports it
```
