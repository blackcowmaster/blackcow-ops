# Gap Report: install-path-security

| Field | Value |
|---|---|
| **Generated** | 2026-06-27 |
| **Plan Items** | 6 |
| **Implemented** | 6 |
| **Match Rate** | 100% |

## Gap Matrix Status

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | `--target` + `--install-path` alias + validation | ✅ | `skills/install.sh:125-160` |
| 2 | `resolve_path()` 4-tier fallback | ✅ | `skills/install.sh:27-71` |
| 3 | `validate_install_path()` 7-step | ✅ | `skills/install.sh:73-120` |
| 4 | `test-l1-unit-install-security.sh` | ✅ | 19/19 pass, 100% |
| 5 | Usage comment banner | ✅ | `skills/install.sh:10-12` |
| 6 | Mutual exclusion conflict detection | ✅ | Both orders tested |

## Gate Coverage

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| M1 spec-match | ≥90% | 100% (6/6 items) | ✅ |
| M2 test-pass | 100% | 19/19 | ✅ |
| M3 regression | 0 failures | 0 new regressions | ✅ |
| M4 lint | 0 | 0 syntax errors | ✅ |
| M5 dead-code | — | All 7 validation steps exercised | ✅ |
| S1 dataFlow | — | TARGET_DIR flows through validation | ✅ |
| S3 injection | 0 bypasses | 6/6 vectors blocked | ✅ |

## Known Gaps (Non-blocking)

1. `~` alone (bare tilde) case not explicitly tested (covered by ~/* branch)
2. `resolve_path` tier 3 (readlink) and tier 4 (cd+pwd) fallbacks not exercised on macOS (python3 succeeds first)
3. Residual TOCTOU between validation and `mkdir -p` — inherent to bash, documented in governance
4. Bash 3.2 `declare -A` pre-existing issue (not related to this change)

## PDCA Verdict
**No PDCA cycles needed.** Match rate 100%, all gates pass, all 6 attack vectors blocked.
