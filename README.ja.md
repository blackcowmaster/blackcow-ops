<div align="center">
  <h1>BlackCow Ops</h1>

  <p><strong>BKITに着想を得たエージェントエンジニアリングハーネス。</strong><br />
  Reasonix + DeepSeek向け。</p>

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
> **BlackCow Opsは、完全なplan→execute→verify→evolveパイプラインを形成する6つの自己改善型Reasonixスキル**です。BKIT — 数値しきい値を持つ11ゲート品質分類体系をDeepSeekのコスト優位性に合わせて適用します。
>
> DeepSeekの価格（~$0.14/1M入力トークン）では、15の並列ディスカバリーレーン + 8の敵対的QAエージェント + 7回のPDCAサイクルを**合計$0.03未満**で実行できます。

## インストール

```bash
# Reasonixのスキルディレクトリにクローン
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Reasonixを再起動すると、6つの`blackcow-*`スキルがグローバルで使用可能になります。

## 利用シーン

| シナリオ | 推奨 |
| --- | --- |
| **Reasonix + DeepSeekを使用中** | **ネイティブ。** すべてのモデルティア、コンテキストバジェット、PDCAサイクルがDeepSeekにチューニングされています。6つのスキルを設定なしで使用できます。 |
| **Reasonix + 他のモデルを使用中** | **未検証。** ReasonixはAI SDKを通じて他のプロバイダー（Anthropic、OpenAI、Google等）もサポートしていますが、BlackCowはDeepSeekでのみテストされています。他のモデルを試す場合は、各スキルのYAML frontmatterの`model_tiers`を編集し、コンテキストバジェットを調整してください。結果は保証できません。 |
| **Claude Code、Codex CLI、OpenCodeなどの他のハーネスを使用中** | **移植が必要。** BKIT方法論は特定のハーネスに依存しません。現在の`.md`スキルファイルはReasonixネイティブです — `task`、`edit_file`、`multi_edit`などのツール呼び出しを対象ハーネス用に書き直す必要があります。 |
| **11ゲート品質方法論だけが必要** | **無料。** `docs/BKIT.md`をお読みください — 分類体系、しきい値、監査エージェントの設計が文書化されています。Apache 2.0。 |

## コマンド

| コマンド | 機能 |
| --- | --- |
| `blackcow-plan` | 戦略プランナー。コードベースを10の観点から分析し、3つのアーキテクチャ案を提案、判断可能な計画書を作成。製品コードは一切編集しません。 |
| `blackcow-loop` | 実行エンジン。TDD + Hashlineコンテンツ検証 + PDCAイテレーター + 10エージェント敵対的QA。11ゲートすべてがしきい値を超える証拠を生成するまで停止しません。 |
| `blackcow-qa` | 品質保証。数値しきい値による11ゲート評価、L1-L5テストピラミッド生成、証拠→メモリパイプラインとトレンド分析。 |
| `blackcow-librarian` | プロジェクトメモリ。階層型AGENTS.mdの生成、コードベース構造のキャッシュ（.omo/library/）、git diffによる増分更新。 |
| `blackcow-skill-review` | メタ監査者。スキルファイルの構文、ゲート完全性、並列性、コスト効率、陳腐化を6つの並列レーン（5監査 + 1 devil's advocate）で分析。編集不可 — レポートのみ出力。 |
| `blackcow-skill-evolver` | 安全な進化エンジン。レビューレポートを読み取り、承認された修正を3重の安全機構（スコープロック → バックアップ → 承認 → 検証）で適用。 |

## パイプライン

```
blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
    (設計)          (実行)          (検証)

blackcow-skill-review ──→ blackcow-skill-evolver
      (スキル監査)            (スキル修正)
```

最初の3つは**プロダクトサイクル** — コードに対して動作します。後の2つは**メタサイクル** — スキルが自身を監査し改善します。`blackcow-librarian`がコードベースをキャッシュするため、サイクルごとにコストが減少します。

## クイックスタート

```
# 1. コードベースをキャッシュ（初回のみ）
blackcow-librarian --command=init-deep

# 2. 機能を計画
blackcow-plan "OAuth2によるユーザー認証を追加"

# 3. 計画を実行
blackcow-loop "Execute plans/user-auth.md" --trust-level=2

# 4. 品質を検証
blackcow-qa "src/auth/"

# 5. スキル自身を監査
blackcow-skill-review --all
blackcow-skill-evolver .omo/meta-review/review-*.md --approve
```

## 呼び出し方法（Reasonix）

BlackCowスキルはReasonixスキルファイルです。`run_skill`ツールまたは`/`スラッシュショートカットで呼び出します：

```
run_skill({ name: "blackcow-plan", arguments: "OAuth2認証を追加" })
run_skill({ name: "blackcow-loop", arguments: "Execute plans/auth.md --trust-level=2" })
run_skill({ name: "blackcow-qa", arguments: "src/auth/" })
```

Reasonixがスキルをインデックスしていれば：

```
/blackcow-plan OAuth2認証を追加
/blackcow-loop Execute plans/auth.md --trust-level=2
/blackcow-qa src/auth/
```

## 提供機能

| 機能 | 説明 |
| --- | --- |
| **BKIT 11ゲート品質** | M1-M5（実装）、S1-S3（セキュリティ）、P1-P3（パフォーマンス）。すべてのゲートに数値しきい値、専任の監査サブエージェント、検証可能な証拠があります。ゲート未通過 = DONE不可。 |
| **並列実行** | 5-15のディスカバリーレーン、3-5の敵対的レビュアー、8のQAエージェント — すべて`run_in_background=true`でバッチ発射。 |
| **信頼レベル（L0-L4）** | 適応的自律性：L0手動 → L4完全自動。過去の成功率に基づいてPDCAサイクルを自動調整。 |
| **Hashline検証** | すべての`edit_file`呼び出し前にコンテンツスナップショット + 事後検証ガード。OmOのHarness Problemソリューションに触発。 |
| **Red Team PoC** | 2名のエクスプロイトエンジニアがS1/S2/S3の検出結果に対して実用的なペイロードを試行。誤検出を下方修正、確定エクスプロイトを上方修正。 |
| **IntentGate（Phase -1）** | 6クラスの意図検出（パフォーマンス/バグ/機能/セキュリティ/品質/緊急）が計画前に実行 — 誤った方向へのサイクルを防止。 |
| **コスト帰属** | ゲート別、フェーズ別のトークン使用量を実績vs予算で比較。呼び出し間のJSONLトレンド追跡。 |
| **自己改善** | スキルが自身を監査し、改善案を提案し、バックアップ/承認/検証ゲートを通じて安全に進化。 |
| **チェックポイント/再開** | フェーズレベルのチェックポイントとL3+での再開サポート。セッションクラッシュやコンテキストウィンドウオーバーフローを生き延びます。 |
| **DAG依存関係** | 複雑なマルチフィーチャースプリントのための`depends_on`構文とクリティカルパス分析。 |

## アーキテクチャ

```
blackcow-ops/
├── skills/                          ← 6つのスキルファイル（Reasonix互換Markdown）
│   ├── blackcow-plan.md             ← 戦略プランナー（Phase -1 ～ Phase 5）
│   ├── blackcow-loop.md             ← 実行エンジン（Phase 0 ～ Phase 9）
│   ├── blackcow-qa.md               ← 品質保証（Phase 0 ～ Phase 3）
│   ├── blackcow-skill-review.md     ← メタ監査者（6並列レビューレーン）
│   ├── blackcow-skill-evolver.md    ← 安全進化エンジン（7フェーズ、3重安全）
│   └── blackcow-librarian.md        ← プロジェクトメモリ（5コマンド、7フェーズ）
├── docs/
│   └── BKIT.md                      ← 11ゲート分類体系リファレンス
├── README.md
├── README.ko.md
├── README.ja.md
├── README.zh-cn.md
├── LICENSE
└── NOTICE
```

## なぜDeepSeekか？

BlackCowは**無駄にできるほど安価な**モデルのために設計されました。DeepSeekの公開価格（~$0.14/1M入力トークン）は、フロンティアモデルではコスト的に困難なパターンを可能にします：

| パターン | 意義 |
| --- | --- |
| 15並列ディスカバリーレーン | 毎回のフルスペクトルコードベース分析 |
| 8 QAエージェント + 2 PoCエンジニア | すべてのゲートを監査、すべてのエクスプロイトを試行 |
| 7 PDCAサイクル | 「十分良い」で妥協しない |
| 毎呼び出しのメタレビュー | 継続的な自己改善ループ |

> **plan→execute→verify 1サイクルの推定コスト**: $0.03未満（DeepSeek）。これはトークン数に基づく推定であり、実測値ではありません。実際のコストはプロジェクトの規模とタスクの複雑さによって変動します。

## 競合比較

| | BlackCow Ops | [OmO / LazyCodeX](https://github.com/code-yeongyu/oh-my-openagent) | [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code) | [BKIT](https://github.com/popup-studio-ai/bkit-claude-code) |
| --- | --- | --- | --- | --- |
| **プラットフォーム** | Reasonix + DeepSeek | OpenCode + Codex CLI | スタンドアロン（Rust+TS） | Claude Code |
| **品質フレームワーク** | 11ゲート（M/S/P） | なし | なし | 11ゲート（M1-M10+S1） |
| **自己改善** | あり — スキル監査と進化 | なし | なし | なし |
| **サイクルあたりのコスト** | ~$0.03 推定 | プロバイダ依存 | プロバイダ依存 | プロバイダ依存 |
| **意図分析** | あり — IntentGate（6クラス） | なし | 部分的 | あり — Intent Router |
| **Red Team PoC** | あり — エクスプロイトエンジニア | あり — Security Research | なし | なし |
| **Hashline検証** | あり（Reasonix適応） | あり（ネイティブ） | なし | なし |
| **チェックポイント/再開** | あり（L3+） | あり — Session Recovery | プロバイダ再試行 | あり — Sprint resume |
| **ループエンジニアリング** | 7サイクル適応型PDCA | 500回Ralph Loop | ultragoal revision | 5サイクルPDCA |

## BlackCowとは？

**BlackCow Ops**は、BKIT品質方法論をReasonixエージェントランタイムに実装し、DeepSeekのコストプロファイルに最適化したものです。

> *「OmOはオーケストレーションを教えてくれた。BKITはゲーティングを教えてくれた。DeepSeekはトークンを数えるのをやめろと教えてくれた。BlackCowは三つすべてをやる。」*

## 謝辞

BlackCow Opsは以下のプロジェクトのアイデアに基づいています：

- **[BKIT by POPUP STUDIO](https://github.com/popup-studio-ai/bkit-claude-code)** — オリジナルの11ゲート品質分類体系とPDCA方法論。BlackCowはM1-M10+S1をM1-M5（実装）+ S1-S3（セキュリティ）+ P1-P3（パフォーマンス）に拡張し、Reasonixネイティブ実装を提供します。Apache 2.0。
- **[OmO / oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)** — ディシプリンエージェント、並列オーケストレーション、Hashlineコンテンツ検証、hyperplan敵対的レビューのコンセプトに触発。OmOのソースコードは含まれていません。ライセンスはupstreamを参照。
- **[Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)** — deep-interview、tmuxベースワーカー、外部ハーネス哲学。
- **[pi-team](https://github.com/minzique/pi-team)** — トランスクリプトベースのマルチエージェントラウンドロビン通信。
- **[Claw Code](https://github.com/ultraworkers/claw-code)** — エージェント管理の美術館展示 — 自己改善ループにインスピレーションを与えました。

## ライセンス

Apache 2.0 — [LICENSE](LICENSE)および[NOTICE](NOTICE)を参照。

---

<div align="center">
  <p>BlackCow Opsで作られ、BlackCow Opsによって作られています。</p>
</div>
