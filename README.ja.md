<div align="center">
  <h1>BlackCow Ops</h1>

  <p><strong>BKITベースのエージェントエンジニアリングハーネス。</strong><br />
  Reasonix + DeepSeekネイティブ。</p>

  <p>
    <a href="#インストール">インストール</a>
    ·
    <a href="#クイックスタート">クイックスタート</a>
    ·
    <a href="README.md">English</a>
    ·
    <a href="README.ko.md">한국어</a>
    ·
    <a href="README.zh-cn.md">简体中文</a>
  </p>
</div>

<hr />

> [!NOTE]
> **BlackCow Opsは7つの自己改善型Reasonixスキル**で構成される **govern → plan → execute → verify → evolve** パイプラインです。BKIT 11ゲート品質体系(M1-M5実装, S1-S3セキュリティ, P1-P3パフォーマンス)をDeepSeekのコスト優位性(~$0.14/1M flash, ~$0.435/1M pro)に最適化。FASTモードのタイポ修正は~$0.001、FULLモードのマルチファイル機能は~$0.03です。

## プロジェクト状況

| 指標 | スコア |
| --- | --- |
| **BlackCow Ops スコア** | **96.2 / 100** |
| **目標** | ~~90点突破~~ ✅ 達成！ |

> 11品質次元の総合指標。[品質スコア進化](#品質スコア進化)を参照。

## インストール

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Reasonix再起動後、7つの`blackcow-*`スキルがグローバルで使用可能です。

## 利用シーン

| 状況 | 推奨 |
| --- | --- |
| **Reasonix + DeepSeek** | **即使用可能。** DeepSeekに最適化済み。7スキルをゼロ設定で。 |
| **Reasonix + 他モデル** | **未検証。** モデル別チューニング必要。YAMLの`model_tiers`を修正。 |
| **Claude Code, Codex CLI等** | **移植必要。** BKIT方法論はハーネス非依存。ツール呼び出しの書き換えが必要。 |
| **11ゲート方法論のみ** | **無料。** `docs/BKIT.md`参照。Apache 2.0。 |

## コマンド

| コマンド | 説明 |
| --- | --- |
| `blackcow-governor` | パイプライン制御。モード/ゲート/Oレベル/PDCA予算選択。障害パターンメモリとROI履歴ロード。 |
| `blackcow-plan` | 戦略設計。3段階プログレッシブワイドニング、10ディスカバリーレーン、3アーキテクチャオプション。 |
| `blackcow-loop` | 実行エンジン。5モード、ネイティブreview+security_review、Phase 2.2 Root Cause、Findings Gate、O0-O4検証。 |
| `blackcow-qa` | 品質保証。条件付きゲート選択、11ゲート評価、L1-L5テストピラミッド。 |
| `blackcow-librarian` | プロジェクトメモリ。7コマンド、構造キャッシュ、障害パターンメモリ、トレンド分析。 |
| `blackcow-skill-review` | メタ監査。トレンド追跡、陳腐化検出。⚠️ スコア変動あり — トレンド分析用のみ。 |
| `blackcow-skill-evolver` | 安全進化エンジン。3重安全(スコープロック→バックアップ→承認→検証)。 |

## パイプライン

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (事前チェック)       (設計)          (実行)          (検証)

blackcow-skill-review ──→ blackcow-skill-evolver
      (スキル監査)            (スキル修正)

                    blackcow-librarian
               (キャッシュ + メモリ + トレンド)
```

## クイックスタート

```
# 1. コードベースキャッシュ (初回のみ)
blackcow-librarian --command=init-deep

# 2. 事前チェック
blackcow-governor "OAuth2ユーザー認証を追加"

# 3. 機能設計
blackcow-plan "OAuth2ユーザー認証を追加" --govern=auth

# 4. 計画実行
blackcow-loop "Execute plans/user-auth.md" --mode=standard --trust-level=2

# 5. 品質検証
blackcow-qa "src/auth/" --gates=auto
```

## Reasonixでの呼び出し

```
run_skill({ name: "blackcow-plan", arguments: "OAuth2認証を追加" })
```

またはスラッシュショートカット: `/blackcow-plan OAuth2認証を追加`

## 主な機能

| 機能 | 説明 |
| --- | --- |
| **BKIT 11ゲート** | M1-M5(実装), S1-S3(セキュリティ), P1-P3(パフォーマンス)。全ゲートに数値閾値と証拠。 |
| **5実行モード** | FAST → STANDARD → FULL → SIEGE → ESCALATE。モード別レーン/ゲート/PDCA予算。 |
| **条件付きゲート選択** | git diff信号 + 言語別パターンで必要なゲートのみ自動選択。 |
| **プログレッシブワイドニング** | 3段階の不確実性ベース探索。最も安い方法から、必要な時だけ拡張。 |
| **O0-O4可観測検証** | O0(なし) → O4(ブラウザ自動化)。利用可能ツールを自動検出、正直なキャップ。 |
| **Findings Gate** | PDCA中に発見された全ギャップを追跡。未解決findingが残ると完了をブロック。FableCodexパターン採用。 |
| **ネイティブツール統合** | Loop Phase 5でReasonix `review` + `security_review` を使用 — より速く正確で安価。 |
| **PDCA証拠規律** | ハードストップルール: 証拠なし→停止、同一失敗×2→ESCALATE。 |

## アーキテクチャ

```
blackcow-ops/
├── skills/                          ← 7スキル + インストーラ
│   ├── blackcow-governor.md         ← パイプライン制御
│   ├── blackcow-plan.md             ← 戦略設計
│   ├── blackcow-loop.md             ← 実行エンジン
│   ├── blackcow-qa.md               ← 品質保証
│   ├── blackcow-librarian.md        ← プロジェクトメモリ
│   ├── blackcow-skill-review.md     ← メタ監査
│   ├── blackcow-skill-evolver.md    ← 安全進化エンジン
│   └── install.sh                   ← クロスプラットフォーム
├── docs/BKIT.md                     ← 11ゲートリファレンス
├── README.md (EN/KO/JA/ZH-CN)
├── LICENSE
└── NOTICE
```

## なぜDeepSeekか？

BlackCowは**無駄にできるほど安い**モデルのために設計されました。

| パターン | 意味 |
| --- | --- |
| 15並列ディスカバリーレーン | 毎回の完全コードベース分析 |
| 8 QA + 2 PoCエージェント | 全ゲート監査、全エクスプロイト試行 |
| 7 PDCAサイクル | 「十分」で妥協しない |
| 毎回のメタレビュー | 継続的自己改善ループ |

> **plan→execute→verify 1サイクル推定コスト**: $0.03未満 (DeepSeek)。トークンカウントベースの推定。

## 品質スコア進化

**スコア駆動の自己進化ループ**(73ラウンド, 38コミット)。各ラウンド: スコア → 弱点特定 → 最小修正 → 再スコア → 改善時のみ採用。

| ラウンド | スコア | 主な改善 |
|---|---:|---:|---|
| baseline | **57.0** | 初期11次元評価 |
| R1-R3 | **71.1** | allowed-tools互換性、クロスプラットフォーム |
| R4-R6 | **84.4** | O0-O4可観測性、証拠インデックス |
| R10 | **90.7** | `blackcow-governor` — パイプライン制御 |
| R21-R40 | **91.4** | 全11次元90+ |
| R51-R55 | **91.5** | Governor E2E検証、フルパイプライン |
| R56-R60 | **93.0** | Failure Pattern Memory稼働、9障害auto-fix |
| R61-R65 | **94.0** | S1+S3ゲート発動、実PDCAサイクル |
| R66-R70 | **95.5** | 7エージェントマルチドメイン、11/11ゲートカバー |
| R71 | **96.0** | O4可観測検証 (puppeteer) |
| R72 | **96.2** | Findings Gate (FableCodex)、TOCTOUバグ修正 |

| 次元 | 基準 (57) | 現在 (96.2) |
|---|---:|---:|---:|
| Reasonixネイティブ | 52 | 91 |
| DeepSeek適合性 | 78 | 92 |
| ループ予算制御 | 48 | 92 |
| プログレッシブワイドニング | 40 | 91 |
| 条件付きゲート選択 | 38 | 91 |
| PDCA証拠規律 | 58 | 91 |
| 可観測検証 | 30 | 90 |
| 証拠圧縮 | 45 | 91 |
| 障害パターンメモリ | 40 | 92 |
| 自己レビュー統合 | 65 | 93 |
| 安全性/幻覚防止 | 80 | 91 |

**+69%改善。評価基準は固定。**

## BlackCowとは？

**BlackCow Ops**はBKIT品質方法論をReasonixエージェントランタイムに実装し、DeepSeekに最適化したものです。

> *「OmOはオーケストレーションを教えてくれた。BKITはゲーティングを教えてくれた。DeepSeekはトークンを数えるのをやめろと教えてくれた。BlackCowは三つすべてをやる。」*

## 謝辞

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — オリジナル11ゲート品質体系。Apache 2.0。
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — ディシプリンエージェント、並列オーケストレーション。
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview、tmuxベースワーカー。
- **[pi-team](https://github.com/minzique/pi-team)** — マルチエージェントラウンドロビン通信。
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — 自己改善ループの着想。

## ライセンス

Apache 2.0 — [LICENSE](LICENSE) および [NOTICE](NOTICE) 参照。

---

<div align="center">
  <p>BlackCow Opsで作り、BlackCow Opsが作りました。</p>
</div>
