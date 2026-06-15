<div align="center">
  <h1>BlackCow Ops</h1>

  <p><strong>BKIT 기반 에이전트 엔지니어링 하네스.</strong><br />
  Reasonix + DeepSeek 네이티브.</p>

  <p>
    <a href="#설치">설치</a>
    ·
    <a href="#빠른-시작">빠른 시작</a>
    ·
    <a href="README.md">English</a>
    ·
    <a href="README.ja.md">日本語</a>
    ·
    <a href="README.zh-cn.md">简体中文</a>
  </p>
</div>

<hr />

> [!NOTE]
> **BlackCow Ops는 7개의 자기 개선형 Reasonix 스킬**로 구성된 **govern → plan → execute → verify → evolve** 파이프라인입니다. BKIT 11-게이트 품질 체계(M1-M5 구현, S1-S3 보안, P1-P3 성능)를 DeepSeek의 비용 이점(~$0.14/1M flash, ~$0.435/1M pro)에 맞게 튜닝했습니다. FAST 모드 오타 수정은 ~$0.001, FULL 모드 다중 파일 기능은 ~$0.03입니다.

## 프로젝트 상태

| 지표 | 점수 |
| --- | --- |
| **BlackCow Ops 점수** | **96.2 / 100** |
| **목표** | ~~90점 돌파~~ ✅ 달성! |

> 11개 품질 차원의 종합 지표. [품질 점수 개선 이력](#품질-점수-개선-이력) 참고.

## 설치

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Reasonix 재시작 후 7개 `blackcow-*` 스킬이 전역에서 사용 가능합니다.

## 사용 시나리오

| 상황 | 권장 |
| --- | --- |
| **Reasonix + DeepSeek** | **즉시 사용.** 모든 설정이 DeepSeek에 최적화됨. 7개 스킬 무설정 사용. |
| **Reasonix + 다른 모델** | **미검증.** 다른 제공사용 튜닝 필요. YAML의 `model_tiers` 수정. |
| **Claude Code, Codex CLI 등** | **포팅 필요.** BKIT 방법론은 하네스 독립적. 도구 호출 재작성 필요. |
| **11-게이트 방법론만** | **무료.** `docs/BKIT.md` 참고. Apache 2.0. |

## 명령어

| 명령어 | 설명 |
| --- | --- |
| `blackcow-governor` | 파이프라인 제어기. 모드/게이트/O-레벨/PDCA 예산 선택. 실패 패턴 메모리와 ROI 이력 로드. |
| `blackcow-plan` | 전략 설계자. 3단계 점진적 확장, 10개 디스커버리 레인, 3가지 아키텍처 옵션. |
| `blackcow-loop` | 실행 엔진. 5개 모드, 네이티브 review+security_review, Phase 2.2 Root Cause, Findings Gate, O0-O4 검증. |
| `blackcow-qa` | 품질 보증. 조건부 게이트 선택, 11-게이트 평가, L1-L5 테스트 피라미드. |
| `blackcow-librarian` | 프로젝트 메모리. 7개 명령어, 구조 캐시, 실패 패턴 메모리, 트렌드 분석. |
| `blackcow-skill-review` | 메타 감사. 트렌드 추적, 진부화 감지. ⚠️ 점수 변동 가능 — 트렌드 분석용으로만 사용. |
| `blackcow-skill-evolver` | 안전 진화 엔진. 3중 안전(범위 잠금→백업→승인→검증). |

## 파이프라인

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (사전 점검)         (설계)          (실행)          (검증)

blackcow-skill-review ──→ blackcow-skill-evolver
      (스킬 감사)              (스킬 수정)

                    blackcow-librarian
               (캐싱 + 메모리 + 트렌드)
```

앞 4개는 **제품 사이클**, 뒤 2개는 **메타 사이클**. Librarian이 모든 것을 뒷받침합니다.

## 빠른 시작

```
# 1. 코드베이스 캐싱 (최초 1회)
blackcow-librarian --command=init-deep

# 2. 사전 점검 (모드/게이트/예산 선택)
blackcow-governor "OAuth2 사용자 인증 추가"

# 3. 기능 설계
blackcow-plan "OAuth2 사용자 인증 추가" --govern=auth

# 4. 계획 실행
blackcow-loop "Execute plans/user-auth.md" --mode=standard --trust-level=2

# 5. 품질 검증
blackcow-qa "src/auth/" --gates=auto

# 6. 스킬 자체 감사
blackcow-skill-review --all
```

## Reasonix에서 호출

```
run_skill({ name: "blackcow-plan", arguments: "OAuth2 인증 추가" })
run_skill({ name: "blackcow-loop", arguments: "Execute plans/auth.md --trust-level=2" })
```

또는 슬래시 단축키: `/blackcow-plan OAuth2 인증 추가`

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| **BKIT 11-게이트** | M1-M5(구현), S1-S3(보안), P1-P3(성능). 모든 게이트에 수치 임계값과 증거 요구. |
| **5개 실행 모드** | FAST → STANDARD → FULL → SIEGE → ESCALATE. 모드별 레인/게이트/PDCA 예산. |
| **조건부 게이트 선택** | git diff 신호 + 언어별 패턴으로 필요한 게이트만 자동 선택. |
| **점진적 확장** | 3단계 불확실성 기반 디스커버리. 가장 저렴한 방법부터, 필요할 때만 확장. |
| **O0-O4 관측 검증** | O0(없음) → O4(브라우저 자동화). 가용 도구 자동 감지, 정직한 캡. |
| **Findings Gate** | PDCA 중 발견된 모든 갭을 추적. 미해결 finding이 있으면 완료 차단. FableCodex 패턴 흡수. |
| **네이티브 도구 통합** | Loop Phase 5에서 Reasonix `review` + `security_review` 사용 — 더 빠르고 정확하고 저렴. |
| **PDCA 증거 규율** | 하드스탑 규칙: 증거 없음→중단, 동일 실패×2→ESCALATE. |
| **실패 패턴 메모리** | 구조화된 실패 기록, 해결 효과성 추적. QA 이력에서 자동 생성. |
| **교차 스킬 증거 계약** | 7개 스킬 간 표준화된 아티팩트 교환. freshness 체크 포함. |

## 아키텍처

```
blackcow-ops/
├── skills/                          ← 7개 스킬 + 설치 스크립트
│   ├── blackcow-governor.md         ← 파이프라인 제어기
│   ├── blackcow-plan.md             ← 전략 설계자
│   ├── blackcow-loop.md             ← 실행 엔진
│   ├── blackcow-qa.md               ← 품질 보증
│   ├── blackcow-librarian.md        ← 프로젝트 메모리
│   ├── blackcow-skill-review.md     ← 메타 감사
│   ├── blackcow-skill-evolver.md    ← 안전 진화 엔진
│   └── install.sh                   ← 크로스플랫폼 설치
├── docs/BKIT.md                     ← 11-게이트 레퍼런스
├── README.md (EN/KO/JA/ZH-CN)
├── LICENSE
└── NOTICE
```

## 왜 DeepSeek인가?

BlackCow는 **낭비해도 될 만큼 저렴한** 모델을 위해 설계되었습니다.

| 패턴 | 의미 |
| --- | --- |
| 15개 병렬 디스커버리 레인 | 매번 전체 코드베이스 분석 |
| 8 QA + 2 PoC 에이전트 | 모든 게이트 감사, 모든 익스플로잇 시도 |
| 7회 PDCA 사이클 | "충분히 좋음"에 타협 금지 |
| 호출마다 메타 리뷰 | 지속적 자기 개선 루프 |

> **plan→execute→verify 1사이클 추정 비용**: $0.03 미만 (DeepSeek). 토큰 카운팅 기반 추정치.

## 경쟁 비교

| | BlackCow Ops | OmO / LazyCodeX | Gajae-Code | BKIT |
| --- | --- | --- | --- | --- |
| **플랫폼** | Reasonix + DeepSeek | OpenCode + Codex CLI | 독립형 (Rust+TS) | Claude Code |
| **품질 프레임워크** | 11-Gate (M/S/P) | 없음 | 없음 | 11-Gate |
| **자가 개선** | ✅ 스킬 감사+진화 | ❌ | ❌ | ❌ |
| **사이클당 비용** | ~$0.03 추정 | 제공사 의존 | 제공사 의존 | 제공사 의존 |
| **Red Team PoC** | ✅ 익스플로잇 엔지니어 | ✅ Security Research | ❌ | ❌ |
| **루프 엔지니어링** | 7사이클 적응형 PDCA | 500회 Ralph Loop | ultragoal revision | 5사이클 PDCA |

## 품질 점수 개선 이력

**점수 기반 자기 개선 루프**(73라운드, 38커밋). 매 라운드: 점수 → 약점 식별 → 최소 수정 → 재측정 → 개선 시에만 채택.

| 라운드 | 점수 | 주요 개선 |
|---|---:|---:|---|
| baseline | **57.0** | 최초 11-dimension 평가 |
| R1-R3 | **71.1** | allowed-tools 호환성, 크로스플랫폼 install.sh |
| R4-R6 | **84.4** | O0-O4 observable, evidence index, failure-pattern memory |
| R7-R9 | **87.6** | Progressive widening, PDCA evidence discipline |
| R10 | **90.7** | `blackcow-governor` — 파이프라인 제어기 |
| R21-R40 | **91.4** | 11개 차원 전부 90+ |
| R51-R55 | **91.5** | Governor E2E 검증, 풀파이프라인, ESCALATE |
| R56-R60 | **93.0** | Failure Pattern Memory 가동, 9개 실패 auto-fix |
| R61-R65 | **94.0** | S1+S3 gate 트리거, 실제 PDCA 사이클 |
| R66-R70 | **95.5** | 7-agent 멀티도메인, FAN-OUT, 11/11 게이트 커버 |
| R71 | **96.0** | O4 observable 검증 (puppeteer) |
| R72 | **96.2** | Findings Gate (FableCodex), TOCTOU 버그 발견+수정 |

| 차원 | 기준 (57) | 현재 (96.2) |
|---|---:|---:|---:|
| Reasonix-native | 52 | 91 |
| DeepSeek fit | 78 | 92 |
| Loop budget control | 48 | 92 |
| Progressive widening | 40 | 91 |
| Conditional gate selection | 38 | 91 |
| PDCA evidence discipline | 58 | 91 |
| Observable verification | 30 | 90 |
| Evidence compaction | 45 | 91 |
| Failure-pattern memory | 40 | 92 |
| Self-review integration | 65 | 93 |
| Safety / anti-hallucination | 80 | 91 |

**+69% 개선. 기준표 고정 — 움직이는 골대 없음.**

## BlackCow란?

**BlackCow Ops**는 BKIT 품질 방법론을 Reasonix 에이전트 런타임에 구현하고 DeepSeek에 최적화한 것입니다.

> *"OmO는 오케스트레이션을 가르쳐줬다. BKIT는 게이팅을 가르쳐줬다. DeepSeek은 토큰 세기를 멈추라고 가르쳐줬다. BlackCow는 셋 다 한다."*

## 감사의 말

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — 원조 11-게이트 품질 분류 체계. Apache 2.0.
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — 디시플린 에이전트, 병렬 오케스트레이션.
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview, tmux 기반 워커.
- **[pi-team](https://github.com/minzique/pi-team)** — 멀티에이전트 라운드로빈 통신.
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — 자기 개선 루프 영감.

## 라이선스

Apache 2.0 — [LICENSE](LICENSE) 및 [NOTICE](NOTICE) 참조.

---

<div align="center">
  <p>BlackCow Ops로 만들고, BlackCow Ops가 만들었습니다.</p>
</div>
