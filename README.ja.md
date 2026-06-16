<div align="center">
  <h1>BlackCow Ops</h1>
  <p><strong>Reasonix + DeepSeekのための7つの自己改善型ワークフロースキル。</strong></p>
  <p>
    <a href="#インストール">インストール</a> · <a href="#クイックスタート">クイックスタート</a> ·
    <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh-cn.md">简体中文</a>
  </p>
</div>

---

## 概要

BlackCow Opsは、コーディングタスクのための **govern → plan → execute → verify → evolve** パイプラインを形成する7つのReasonixスキルです。BKIT 11ゲート品質体系をDeepSeekのコスト優位性に合わせて調整しています。タイポ修正は約$0.001、マルチファイル機能は約$0.03で処理されます。

**正直なスコア: 89.8/100**（11次元平均）。評価基準は固定 — ゴールポスト移動なし。

> 手順はモデルの天井を上げられません。天井までの道を照らすだけです。BlackCowは限界に達したらエスカレーションします。決して見せかけません。

## スキル

| スキル | 役割 |
|---|---|
| `blackcow-governor` | 事前チェック制御。作業前にモード、ゲート、可観測レベル、PDCA予算を選択。 |
| `blackcow-plan` | 戦略設計。プログレッシブワイドニング、アーキテクチャオプション、決定完結型計画。 |
| `blackcow-loop` | 実行エンジン。5モード(FAST~ESCALATE)、PDCA、Findings Gate、O0-O4検証。 |
| `blackcow-qa` | 品質保証。数値閾値ベースの条件付き11ゲート評価。 |
| `blackcow-librarian` | プロジェクトメモリ。構造キャッシュ、障害パターンメモリ、トレンド分析。 |
| `blackcow-skill-review` | メタ監査。スキル自体のトレンド追跡と陳腐化検出。 |
| `blackcow-skill-evolver` | 安全進化エンジン。レビュー済み変更を3重安全ゲートで適用。 |

## インストール

```bash
git clone https://github.com/blackcowmaster/blackcow-ops.git
cp blackcow-ops/skills/*.md ~/.reasonix/skills/
```

Reasonixを再起動すると、7つのスキルがグローバルで使用可能になります。

## クイックスタート

```
# コードベースキャッシュ（初回のみ）
blackcow-librarian --command=init-deep

# タスク制御（モード、ゲート、予算）
blackcow-governor "OAuth2認証を追加"

# 実装計画
blackcow-plan "OAuth2認証を追加" --govern=oauth

# 計画実行
blackcow-loop "Execute plans/oauth.md" --mode=standard --trust-level=2

# 品質検証
blackcow-qa "src/auth/" --gates=auto
```

`run_skill` または `/` ショートカットで呼出: `/blackcow-plan OAuth2認証を追加`

## 主な強み

- **PRDから実装まで。** 仕様を読み、技術スタックを推論し、独立した単位に分解して並列計画を立てます。決める前に尋ねます — ユーザーのスタックを黙って決めません。
- **DeepSeekコスト最適化。** 5つの実行モードがタイポ修正$0.001からフルセキュリティ監査$0.10までスケール。プログレッシブワイドニングで必要な時だけコストが増加。
- **11ゲート品質。** M1-M5(実装)、S1-S3(セキュリティ)、P1-P3(パフォーマンス)。全ゲートに数値閾値と証拠が必要。
- **Findings Gate。** レビュー中に発見された問題は追跡され、完了前に解決必須。既知のバグを黙認しません。
- **障害パターンメモリ。** 過去の障害が効果スコア付きで記録。高効果の修正は自動適用、低効果パターンはエスカレーション。
- **Subagent O4検証。** Playwright CLI(`npx playwright screenshot`)でブラウザスクリーンショット — サブエージェントでネイティブpuppeteer依存不要。
- **CLIブリッジ。** サブエージェントは`run_command`で任意のCLIツール(`supabase`、`aws`、`firebase`、`docker`)を使用可能。認証ツールはユーザー確認が必要。
- **自己監査。** 全スキルに構造化された自己監査チェックリスト。スキルが自らをレビューし進化。

## アーキテクチャ

```
blackcow-governor ──→ blackcow-plan ──→ blackcow-loop ──→ blackcow-qa
   (事前チェック)      (設計)          (実行)          (検証)

blackcow-skill-review ──→ blackcow-skill-evolver
      (スキル監査)            (スキル修正)

                    blackcow-librarian
               (キャッシュ + メモリ + トレンド)
```

## なぜDeepSeekか

BlackCowは無駄にできるほど安いモデルのために設計されました。DeepSeek価格(flash ~$0.14/1M入力)は、他ではコスト負担が大きいパターンを可能にします：15並列ディスカバリーレーン、8 QAエージェント、7 PDCAサイクル。

## 参照

- **[BKIT](https://github.com/popup-studio-ai/bkit-claude-code)** — 11ゲート品質体系。Apache 2.0。

## ライセンス

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)

---

<div align="center"><p>BlackCow Opsで作り、BlackCow Opsが作りました。</p></div>
