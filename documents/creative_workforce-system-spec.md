# Creative Workforce System Specification

最終更新: 2025-02-14  
本ドキュメントは Creative Workforce PoC の現行仕様を統合したリファレンスです。前世代の分散した仕様書（PoC仕様書.md / ディレクトリとアーキテクチャ案.md / frontend-uiux-plan.md）は本書に統合されました。

---

## 1. システム概要

| 項目 | 内容 |
| --- | --- |
| 目的 | 映像作品のプリプロダクションにおける脚本/設定/キーフレームなどの生成フローを PoC レベルで検証 |
| 利用者 | バックエンド/エージェント開発者、PM、PoC デモ担当者 |
| コア機能 | プロジェクト管理 / 成果物生成 (LLM/画像) / 進捗管理 / 会話エージェントとの連携 |
| 技術スタック | FastAPI + LangGraph (backend), Next.js 14 App Router + Tailwind CSS + tRPC (frontend), PostgreSQL / MinIO / Redis (local), Cloud SQL / GCS / Cloud Tasks (GCP) |

---

## 2. リポジトリ構成

```
creative_workforce/
├── backend/                 # FastAPI + LangGraph
│   ├── app/
│   │   ├── api/             # REST/tRPC エンドポイント
│   │   ├── agents/          # 成果物ごとの LangGraph エージェント
│   │   ├── core/            # 設定・DI・共通処理
│   │   ├── models/          # Pydantic/SQLModel スキーマ
│   │   ├── services/        # Storage/VectorStore/TaskQueue の抽象化
│   │   └── workers/         # 非同期ジョブ処理
│   ├── tests/               # pytest スイート（API / services / agents）
│   └── scripts/             # DBマイグレーション・セットアップ
├── frontend/                # Next.js 14 + Tailwind
│   ├── app/                 # App Router ルート
│   │   ├── layout.tsx       # Tailwind AppShell
│   │   └── page.tsx         # Dashboard クライアントページ
│   ├── components/          # Dashboard / Layout コンポーネント
│   ├── lib/                 # tRPC クライアント、型定義
│   ├── tests/               # Vitest (最小スモーク含む)
│   └── tailwind.config.ts   # デザイン設定
├── infrastructure/          # docker-compose, Terraform, GitHub Actions
├── config/                  # env テンプレート / プロンプト
├── documents/               # 本仕様書 / 提案書 / ガイド
└── scripts/                 # ルートスクリプト
```

---

## 3. フロントエンド仕様

### 3.1 UIレイアウト
- `AppShell` コンポーネントがサイドバー・ヘッダー・メインコンテンツを統合。
- Tailwind CSS ベースで、ブランドカラー `brand-500 (#6777f7)` を主要アクセントに使用。
- ヒーローセクション (`DashboardHero`) で統計カード（プロジェクト数 / 生成済み成果物 / 未完了テンプレート）を表示。
- `ProjectSidebar` ではプロジェクト作成フォームと一覧をカードスタイルで表示。モバイル時はヒーロー下に折りたたみ表示。
- メインコンテンツは以下のセクションで構成:
  1. `ProjectOverview`: 選択プロジェクトの概要カード
  2. `GenerationPanel`: エピソード入力、生成指示、テンプレートボタン、キュー保留バナー
  3. `ArtifactTable`: 成果物リスト（テンプレート / エピソード / バージョン / 表示）
  4. `ProgressSummary`: グローバル/エピソード別の完了・未完了テンプレート
  5. `ArtifactPreview`: テキスト or 画像のプレビュー (`next/image` + base64)
  6. `ChatPanel`: tRPC ベースのチャット、メッセージ、イベントログ

### 3.2 状態管理と API アクセス
- React Hooks (`useState`, `useEffect`, `useMemo`, `useCallback`) を利用。
- データフェッチ:
  - プロジェクト一覧: `GET /api/projects`
  - 成果物リスト: `GET /api/projects/{id}/artifacts`
  - 進捗情報: `GET /api/projects/{id}/progress`
  - 成果物詳細: `GET /api/projects/{projectId}/artifacts/{artifactId}`
  - 生成リクエスト: `POST /api/projects/{id}/artifacts/{template-code}/generate`
  - キーフレームワーカー: `POST /api/tasks/generate-keyframe`
- チャット API は `trpc.chat.*` クライアントを経由。
- `NEXT_PUBLIC_API_BASE_URL` が API のベース URL。未設定時は `http://localhost:8000/api`。

### 3.3 テンプレート定義
```ts
const TEMPLATES = [
  { code: "overall_spec", label: "作品全体仕様書" },
  { code: "character_design", label: "キャラクター設定" },
  { code: "background_sample", label: "背景サンプル" },
  { code: "episode_summary", label: "エピソード概要", requiresEpisode: true },
  { code: "episode_script", label: "エピソード脚本", requiresEpisode: true },
  { code: "storyboard_table", label: "絵コンテ表", requiresEpisode: true },
  { code: "keyframe_image", label: "キーフレーム画像", requiresEpisode: true, kind: "image" },
];
```

### 3.4 主要な UX ポイント
- 初回ロード時に最初のプロジェクトへ自動フォーカス。
- `keyframe_image` が 202 応答の場合、タスク保留バナーを表示しワーカー実行を案内。
- 成果物プレビューはテキスト / 画像を自動判別 (`is_binary` フラグ)。
- アラートメッセージは AppShell の `message` スロットでバナー表示。

---

## 4. バックエンド仕様

### 4.1 API サマリー

| Method | Path | 概要 |
| --- | --- | --- |
| GET | `/api/projects` | プロジェクト一覧取得 |
| POST | `/api/projects` | プロジェクト作成 |
| GET | `/api/projects/{project_id}/artifacts` | 成果物一覧取得 |
| GET | `/api/projects/{project_id}/artifacts/{artifact_id}` | 成果物詳細取得 |
| POST | `/api/projects/{project_id}/artifacts/{template_code}/generate` | テンプレート成果物生成 |
| GET | `/api/projects/{project_id}/progress` | テンプレート進捗 |
| POST | `/api/tasks/generate-keyframe` | キーフレーム生成ワーカー起動 |
| tRPC | `chat.*` | チャットセッション/メッセージ/イベント CRUD |

### 4.2 ドメインモデル（抜粋）
- `Project`: id, name, description, episodes_planned, created_at, updated_at
- `Artifact`: id, project_id, template_code, episode, version, status, storage_path, created_by, created_at
- `Progress`: global/episodes の完了・未完了テンプレート配列
- `ChatSession`, `ChatMessage`, `ChatEvent`

### 4.3 LangGraph エージェント
- テキスト成果物: GPT/Gemini を想定したプリセット Prompt + Tool Chain。
- 画像成果物: `generate_keyframe` タスクとしてキュー投入。ワーカーが Gemini Image API を模擬。
- 依存関係: StorageService (MinIO/GCS), VectorStoreService (Qdrant/Vertex AI), TaskQueueService (Redis/Cloud Tasks)。

### 4.4 環境切り替え
- `ENV_TARGET=local|gcp` に応じてサービス実装を切替。
- ローカル: PostgreSQL (docker-compose), MinIO, Redis Queue。
- GCP: Cloud SQL, GCS, Cloud Tasks + Cloud Run Jobs。

---

## 5. DevOps / CI

- **ローカル起動**
  1. `uv sync` / `pnpm install`
  2. `docker-compose up -d postgres minio redis`
  3. `uv run fastapi dev` / `pnpm dev`
- **テスト**
  - Backend: `uv run pytest`
  - Frontend: `pnpm test` (Vitest、最低限のスモーク含む)
- **CI**
  - GitHub Actions (`infrastructure/github/ci.yml`) で `uv run pytest` と `pnpm lint` を実施。
  - 今後 `pnpm test` を追加予定。
- **デプロイ予定**
  - Terraform + Cloud Build パイプラインを整備し Cloud Run へデプロイ。

---

## 6. ドキュメント運用

| 種別 | ファイル | 内容 |
| --- | --- | --- |
| 仕様 | `documents/creative_workforce-system-spec.md` (本書) | 最新仕様 |
| 会話仕様 | `documents/chat-conversation-spec.md` | tRPC / LangGraph 会話仕様 |
| スタートガイド | `documents/スタートガイド.md` | セットアップ手順 |
| 企画・提案 | `documents/企画書.md`, `documents/提案書.md` | ビジネス向け資料 |

---

## 7. ロードマップ（抜粋）

1. **会話体験のリッチ化**: ストリーミング、イベントタイムライン、テンプレート再生成ガイド。
2. **成果物メタ情報の追加**: 更新履歴・担当者を表示しレビュー導線を構築。
3. **認証/権限**: Firebase/Auth0 を利用したログインとプロジェクト ACL。
4. **IaC/デプロイ**: Terraform + Cloud Build パイプラインで GCP デプロイ自動化。
5. **UX 計測**: 操作ログ、ヒートマップ、アクセシビリティ監査を導入。

---

## 8. 廃止ドキュメント

以下のファイルは内容を統合済みのため削除されました:
- `documents/PoC仕様書.md`
- `documents/ディレクトリとアーキテクチャ案.md`
- `documents/frontend-uiux-plan.md`

最新仕様は本書および関連ドキュメントを参照してください。
