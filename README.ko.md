<div align="center">
  <h1>BlackCow Ops</h1>
  <p><strong>Reasonix + DeepSeek를 위한 9개의 자기 개선형 워크플로우 스킬.</strong></p>
  <p>
    <a href="#설치">설치</a> · <a href="#빠른-시작">빠른 시작</a> ·
    <a href="README.md">English</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh-cn.md">简体中文</a>
  </p>
</div>

---

## 무엇인가

BlackCow Ops는 코딩 작업을 위한 **govern → plan → execute → verify → evolve** 파이프라인을 형성하는 9개의 Reasonix 스킬입니다. BKIT 11-게이트 품질 체계를 DeepSeek의 비용 이점에 맞게 튜닝했습니다. 오타 수정은 약 $0.001, 다중 파일 기능은 약 $0.03에 처리됩니다.

**솔직한 점수: 90.6/100** (11차원 평균). 기준표 고정 — 움직이는 골대 없음.

> 절차는 모델의 천장을 올릴 수 없습니다. 천장까지 가는 길을 밝힐 뿐입니다. BlackCow는 한계에 도달하면 에스컬레이션합니다. 결코 가장하지 않습니다.

## 스킬

| 스킬 | 역할 |
|---|---|
| `blackcow-governor` | 사전 점검 제어기. 작업 전에 모드, 게이트, 관측 수준, PDCA 예산을 선택합니다. |
| `blackcow-plan` | 전략 설계자. 점진적 확장, 아키텍처 옵션, 결정 완결형 계획. |
| `blackcow-loop` | 실행 엔진. TRY 모드(2-3분) + STANDARD/FULL. PDCA, Findings Gate, Visual Review(codex), O0-O4 검증. |
| `blackcow-qa` | 품질 보증. 수치 임계값 기반 조건부 11-게이트 평가. |
| `blackcow-librarian` | 프로젝트 메모리. 구조 캐싱, 실패 패턴 메모리, 트렌드 분석. |
| `blackcow-skill-review` | 메타 감사. 스킬 자체의 트렌드 추적과 진부화 감지. |
| `blackcow-skill-evolver` | 안전 진화 엔진. 검토된 변경사항을 3중 안전 게이트로 적용. |
| `blackcow-app-scraper` | 앱스토어 + 플레이스토어 리뷰 스크래퍼. 메타데이터, 리뷰, 유사 앱을 API 키 없이 추출. |
| `blackcow-app-intel` | 스크래핑된 리뷰에서 시장 인텔리전스 도출. 감정 분석, 불만 랭킹, 약점 맵, PRD 인사이트. |

## 설치

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Reasonix를 재시작하면 9개 스킬이 전역에서 사용 가능합니다.

## 빠른 시작

```
# 코드베이스 캐싱 (최초 1회)
blackcow-librarian --command=init-deep

# 작업 제어 (모드, 게이트, 예산)
blackcow-governor "OAuth2 인증 추가"

# 구현 계획
blackcow-plan "OAuth2 인증 추가" --govern=oauth

# 계획 실행
blackcow-loop "Execute plans/oauth.md" --mode=standard --trust-level=2

# 품질 검증
blackcow-qa "src/auth/" --gates=auto
```

`run_skill` 또는 `/` 단축키로 호출: `/blackcow-plan OAuth2 인증 추가`

## 주요 강점

- **PRD에서 구현까지.** 명세를 읽고 기술 스택을 추론하며 독립적인 단위로 분해하여 병렬 계획을 수립합니다. 결정하기 전에 묻습니다 — 절대 사용자의 스택을 함부로 정하지 않습니다.
- **DeepSeek 비용 최적화.** 5가지 실행 모드가 오타 수정 $0.001부터 전체 보안 감사 $0.10까지 확장됩니다. 점진적 확장으로 필요할 때만 비용이 증가합니다.
- **11-게이트 품질.** M1-M5(구현), S1-S3(보안), P1-P3(성능). 모든 게이트는 수치 임계값과 증거를 요구합니다.
- **Findings gate.** 리뷰 중 발견된 이슈는 추적되며 완료 전에 반드시 해결되어야 합니다. 알려진 버그를 묵인하지 않습니다.
- **실패 패턴 메모리.** 과거 실패가 효과성 점수와 함께 기록됩니다. 높은 효과성의 수정은 자동 적용되고, 낮은 효과성 패턴은 에스컬레이션됩니다.
- **비주얼 리뷰.** DeepSeek V4는 비전 미지원. codex CLI 설치 시 `codex exec --image`로 스크린샷 분석 (가독성, 대비, 여백, 위계). codex 없으면 자동 스킵.
- **시뮬레이터 자동화.** `xcrun simctl`로 부팅, 스크린샷, 앱 실행 — 터미널 안에서 모바일 개발.
- **워크스페이스 격리.** 모든 새 프로젝트는 `~/Downloads/blackcow_project/` 아래 생성 — 도구 디렉토리를 오염시키지 않음.
- **자가 감사.** 모든 스킬에 구조화된 자가 감사 체크리스트가 있습니다. 스킬이 스스로를 검토하고 진화합니다.

## 아키텍처

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (사전 점검)         (설계)          (실행)          (검증)

blackcow-skill-review ──→ blackcow-skill-evolver
      (스킬 감사)              (스킬 수정)

                    blackcow-librarian
               (캐싱 + 메모리 + 트렌드)
```

## 왜 DeepSeek인가

BlackCow는 낭비해도 될 만큼 저렴한 모델을 위해 설계되었습니다. DeepSeek 가격(flash ~$0.14/1M 입력)은 다른 곳에서는 비용 부담이 큰 패턴을 가능하게 합니다: 15개 병렬 디스커버리 레인, 8 QA 에이전트, 7 PDCA 사이클.

## 참고

- **[BKIT](https://github.com/popup-studio-ai/bkit-claude-code)** — 11-게이트 품질 체계. Apache 2.0.

## 라이선스

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)

---

<div align="center"><p>BlackCow Ops로 만들고, BlackCow Ops가 만들었습니다.</p></div>
