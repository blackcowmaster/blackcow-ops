<div align="center">
  <h1>🐂 BlackCow Ops</h1>

  <p><strong>Reasonix + DeepSeek를 위한 에이전트 엔지니어링 하네스.</strong><br />
  BKIT 기반 11-게이트 품질. 자기 개선형 스킬. 사이클당 ~$0.005.</p>

  <p>
    <a href="#-설치">설치</a>
    ·
    <a href="#-빠른-시작">빠른 시작</a>
    ·
    <a href="#-철학">철학</a>
    ·
    <a href="README.md">English</a>
  </p>
</div>

<hr />

> [!NOTE]
> **BlackCow Ops는 6개의 자기 개선형 Reasonix 스킬**로 구성된 plan→execute→verify→evolve 파이프라인입니다. BKIT — 수치 임계값이 있는 11-게이트 품질 분류 체계를 DeepSeek의 비용 이점에 맞게 적용 및 확장했습니다.
>
> DeepSeek 가격(~$0.14/1M 입력 토큰) 기준, 15개 병렬 디스커버리 레인 + 8개 적대적 QA 에이전트 + 7회 PDCA 사이클을 **총 $0.03 미만**으로 실행할 수 있습니다. GPT-5에서 동일한 파이프라인은 $3-5가 소요됩니다.

## 🚀 설치

```bash
# Reasonix 스킬 디렉토리에 클론
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Reasonix를 재시작하면 6개의 `blackcow-*` 스킬이 전역에서 사용 가능합니다.

## ⚡ 명령어

| 명령어 | 설명 |
| --- | --- |
| `blackcow-plan` | 전략 설계자. 코드베이스를 10개 각도에서 분석, 3가지 아키텍처 옵션 제안, 결정 완결형 계획서 작성. 제품 코드 수정 불가. |
| `blackcow-loop` | 실행 엔진. TDD + Hashline 콘텐츠 검증 + PDCA 이터레이터 + 10-에이전트 적대적 QA. 11개 게이트가 모두 증거와 함께 통과할 때까지 멈추지 않음. |
| `blackcow-qa` | 품질 보증. 수치 임계값 기반 11-게이트 평가, L1-L5 테스트 피라미드 생성, 증거→메모리 파이프라인 + 추세 분석. |
| `blackcow-librarian` | 프로젝트 메모리. 계층형 AGENTS.md 생성, 코드베이스 구조 캐싱(.omo/library/), git diff 기반 증분 업데이트. |
| `blackcow-skill-review` | 메타 감사관. 스킬 파일의 구문, 게이트 완전성, 병렬성, 비용 효율, 진부화를 5개 병렬 레인으로 분석. 편집 불가 — 보고서만 출력. |
| `blackcow-skill-evolver` | 안전 진화 엔진. 리뷰 보고서를 읽고 승인된 수정사항을 3중 안전장치(범위 잠금 → 백업 → 승인 → 검증)로 적용. |

## 🔄 파이프라인

```
blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
    (설계)          (실행)          (검증)

blackcow-skill-review ──→ blackcow-skill-evolver
      (스킬 감사)              (스킬 수정)
```

앞 3개는 **제품 사이클** — 코드를 대상으로 작동합니다. 뒤 2개는 **메타 사이클** — 스킬이 스스로를 감사하고 개선합니다. `blackcow-librarian`이 코드베이스를 캐싱하므로 매 사이클마다 비용이 감소합니다.

## 🎯 빠른 시작

```
# 1. 코드베이스 캐싱 (최초 1회)
blackcow-librarian --command=init-deep

# 2. 기능 설계
blackcow-plan "OAuth2 사용자 인증 기능 추가"

# 3. 계획 실행
blackcow-loop "Execute plans/user-auth.md" --trust-level=2

# 4. 품질 검증
blackcow-qa "src/auth/"

# 5. 스킬 자체 감사
blackcow-skill-review --all
blackcow-skill-evolver .omo/meta-review/review-*.md --approve
```

## 🧩 제공 기능

| 기능 | 설명 |
| --- | --- |
| 🎯 **BKIT 11-게이트 품질** | M1-M5 (구현), S1-S3 (보안), P1-P3 (성능). 모든 게이트는 수치 임계값, 전담 감사 하위 에이전트, 검증 가능한 증거를 가집니다. 게이트 미통과 = DONE 불가. |
| 🔀 **병렬 실행** | 5-15개 디스커버리 레인, 3-5개 적대적 리뷰어, 8개 QA 에이전트 — 모두 `run_in_background=true`로 배치 발사. |
| 🎛️ **신뢰 레벨 (L0-L4)** | 적응형 자율성: L0 수동 → L4 완전 자동. 과거 성공률에 따라 PDCA 사이클 자동 조정. |
| 🛡️ **Hashline 검증** | 모든 `edit_file` 호출 전 콘텐츠 스냅샷 + 사후 검증 가드. OmO의 Harness Problem 솔루션에서 영감. |
| 🔴 **Red Team PoC** | 2명의 익스플로잇 엔지니어가 S1/S2/S3 발견사항에 대해 실제 페이로드 시도. 오탐지 하향 조정, 확정된 익스플로잇 상향. |
| 🧠 **IntentGate (Phase -1)** | 6클래스 의도 감지 (성능/버그/기능/보안/품질/긴급) — 계획 수립 전 실행되어 잘못된 방향 방지. |
| 📊 **비용 추적** | 게이트별, Phase별 토큰 사용량을 실제vs예산으로 비교. 호출 간 JSONL 추세 추적. |
| 🔄 **자가 개선** | 스킬이 스스로를 감사하고, 개선안을 제안하며, 백업/승인/검증 게이트를 통해 안전하게 진화. |
| 💾 **체크포인트/재개** | Phase 단위 체크포인트 + L3+ 재개 지원. 세션 충돌과 컨텍스트 윈도우 초과에서 생존. |
| 🧹 **DAG 의존성** | 복잡한 멀티피처 스프린트를 위한 `depends_on` 문법 + 임계경로 분석. |

## 🏗️ 아키텍처

```
blackcow-ops/
├── skills/                          ← 6개 스킬 파일 (Reasonix 호환 Markdown)
│   ├── blackcow-plan.md             ← 전략 설계자 (Phase -1 ~ Phase 5)
│   ├── blackcow-loop.md             ← 실행 엔진 (Phase 0 ~ Phase 9)
│   ├── blackcow-qa.md               ← 품질 보증 (Phase 0 ~ Phase 3)
│   ├── blackcow-skill-review.md     ← 메타 감사관 (5개 병렬 리뷰 레인)
│   ├── blackcow-skill-evolver.md    ← 안전 진화 엔진 (7단계, 3중 안전)
│   └── blackcow-librarian.md        ← 프로젝트 메모리 (5개 명령어, 7단계)
├── docs/
│   └── BKIT.md                      ← 11-게이트 분류 체계 레퍼런스
├── README.md
├── README.ko.md
├── LICENSE
└── NOTICE
```

## 🧠 왜 DeepSeek인가?

BlackCow는 **낭비해도 될 만큼 저렴한** 모델을 위해 처음부터 설계되었습니다. DeepSeek의 ~$0.14/1M 입력 토큰은 GPT-5보다 약 100배 저렴합니다. 이는 경제적으로 가능한 것의 기준을 바꿉니다:

| 패턴 | GPT-5 비용 | DeepSeek 비용 | BlackCow 전략 |
| --- | --- | --- | --- |
| 15개 디스커버리 레인 | ~$1.50 | ~$0.002 | XL에 항상 최대 레인 |
| 8 QA + 2 PoC 에이전트 | ~$1.00 | ~$0.001 | 모든 게이트 매번 실행 |
| 7회 PDCA 사이클 | ~$3.50 | ~$0.005 | "충분히 좋음"에 타협 금지 |
| 호출마다 메타 리뷰 | ~$0.75 | ~$0.001 | 지속적 자기 개선 |

**핵심 통찰**: 품질 게이트 비용이 1센트 미만일 때, 전부 실행합니다. 토큰 수가 아니라 게이트 통과율을 최적화합니다.

## 🆚 경쟁 비교

| | BlackCow Ops | [OmO / LazyCodeX](https://github.com/code-yeongyu/oh-my-openagent) | [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code) | [BKIT](https://github.com/popup-studio-ai/bkit-claude-code) |
| --- | --- | --- | --- | --- |
| **플랫폼** | Reasonix + DeepSeek | OpenCode + Codex CLI | 독립형 (Rust+TS) | Claude Code |
| **품질 프레임워크** | 11-게이트 (M/S/P) | 없음 | 없음 | 11-게이트 (M1-M10+S1) |
| **자가 개선** | ✅ 스킬 감사 및 진화 | ❌ | ❌ | ❌ |
| **사이클당 비용** | ~$0.005 | ~$0.50+ | 제공사 의존 | ~$0.50+ |
| **의도 분석** | ✅ IntentGate (6클래스) | ❌ | 부분적 | ✅ Intent Router |
| **Red Team PoC** | ✅ 익스플로잇 엔지니어 | ✅ 보안 연구 | ❌ | ❌ |
| **Hashline 검증** | ✅ (Reasonix 적용) | ✅ (네이티브) | ❌ | ❌ |
| **체크포인트/재개** | ✅ L3+ | ✅ 세션 복구 | 제공사 재시도 | ✅ 스프린트 재개 |

## 💤 BlackCow란?

**BlackCow Ops**는 BKIT 품질 방법론을 Reasonix 에이전트 런타임에 맞게 패키징하고, DeepSeek의 극단적인 비용 이점에 최적화한 것입니다.

이렇게 생각해보세요: OmO의 에이전트 하네스에 BKIT의 품질 게이트를 추가하고, 15개 병렬 레인이 GPT-5 단일 추론보다 저렴한 모델에 모든 것을 튜닝하면? 그게 BlackCow입니다.

> *"OmO는 오케스트레이션을 가르쳐줬다. BKIT는 게이팅을 가르쳐줬다. DeepSeek은 토큰 세기를 멈추라고 가르쳐줬다. BlackCow는 셋 다 한다."*

## 🙏 감사의 말

BlackCow Ops는 다음 프로젝트들의 아이디어를 기반으로 합니다:

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — 원조 11-게이트 품질 분류 체계와 PDCA 방법론. BlackCow는 M1-M10+S1을 M1-M5(구현) + S1-S3(보안) + P1-P3(성능)으로 확장하고 Reasonix 네이티브 구현을 제공합니다. Apache 2.0.
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — 디시플린 에이전트, 병렬 오케스트레이션, Hashline 콘텐츠 검증, hyperplan 적대적 리뷰.
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview, tmux 기반 워커, 외부 하네스 철학.
- **[pi-team](https://github.com/minzique/pi-team)** — 트랜스크립트 기반 멀티에이전트 라운드로빈 통신.
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — 에이전트가 관리하는 박물관 전시 — 우리의 자기 개선 루프에 영감을 줌.

## 📄 라이선스

Apache 2.0 — [LICENSE](LICENSE) 및 [NOTICE](NOTICE) 참조.

---

<div align="center">
  <p>BlackCow Ops로 만들어졌으며, BlackCow Ops에 의해 만들어졌습니다. 🐂</p>
</div>
