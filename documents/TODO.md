# TODO Roadmap (documents/ディレクトリとアーキテクチャ案.md / PoC仕様書.md)

## ディレクトリ構成案とアーキテクチャ概要.md
### 実装済み
- [x] `backend/` に FastAPI + SQLModel 基盤を整備し、`core/services` でローカル・GCP実装をDI切替可能にした。
- [x] `uv` ベースの依存管理と GitHub Actions (`infrastructure/github/ci.yml`) による `uv run pytest` / `pnpm lint` パイプラインを準備済み。
- [x] `docker-compose.yaml` で PostgreSQL / MinIO / Redis / backend / frontend を一括起動できるローカル環境を用意。
- [x] `scripts/setup_local.sh` などの補助スクリプトを配置済み。
- [x] LangGraphベースのテキスト/画像エージェントとCloud Tasksワーカー、生成API (`/api/projects/{id}/artifacts/{code}/generate`, `/api/tasks/generate-keyframe`) を追加。
- [x] `config/env/.env.(example|local|gcp).example` に環境変数テンプレートを整備。
- [x] 開発者向けスタートガイド (`documents/スタートガイド.md`) を作成。

### 未実装・要対応
- [ ] Chat 体験の高度化（意図確認ダイアログ、ストリーミング、会話ログ管理 UI）は今後の課題。生成APIは `projects` ドメイン中心。
- [ ] Frontend の会話UIは PoC 版。サイドバー統合や制作進行ビューの刷新は未着手。

### 次アクション
1. ChatAPI／会話ルーターとフロントのtRPCクライアントを設計し、エージェント呼び出しを会話体験に統合。
   - [x] 仕様整理（`documents/chat-conversation-spec.md`）
   - [x] バックエンド実装（モデル・API・LangGraph会話エージェント）
   - [x] フロント tRPC クライアント & 会話UI 実装（チャットパネル）
   - [ ] 会話UXの拡張（ストリーミング、テンプレート再確認など）
2. Terraform/Cloud Build 設定を追加し、GCPデプロイフローを定義。
3. フロントエンドの情報設計（チャット、成果物ツリー、進行ビュー）のUI実装を開始。

## PoC仕様書.md
### 実装済み
- [x] プロジェクト・成果物テンプレートを SQLModel (Project/Artifact) と ProgressService で管理し、不足テンプレートを特定できるAPI (`/api/projects/*`) を提供。
- [x] `StorageService` / `VectorStoreService` / `TaskQueueService` の抽象化と `ENV_TARGET` に連動したローカル/GCP実装を整備。
- [x] APIエンドポイントの自動テスト（pytest）と GCP依存サービスのフェイクを用意し、TDD方針を確保。
- [x] LangGraph成果物エージェント（テキスト/画像）、OpenAI/Gemini想定クライアント、Cloud Tasks ワーカーを実装し、生成フローをPoC APIに統合。

### 未実装・要対応
- [ ] 会話UI・成果物エディタ・サイドバーなど Next.js ベースのフロント機能は未実装。成果物アップロードやLLMレス編集も未対応。
- [ ] Chatシナリオ管理、エージェント呼び出しUX、前工程依存チェックなど体験設計はAPIのみでUI/オーケストレーションが未整備。
- [ ] 認証（Firebase/Auth0想定）、ユーザー権限、オフライン用モックアダプタ、AIモデル課金ガードなど運用要件が未着手。
- [ ] GCPデプロイ（Cloud Run / Cloud SQL / Secret Manager 等）のIaCとパイプライン整備が未完了。

### ゴールまでの道筋
1. **体験フロー実装**: Frontend UIとAPIを結合し、プロジェクト作成→成果物生成→不足確認→アップロードの基本動線を成立させる。
2. **エージェント統合**: LangGraphで各成果物エージェントを実装し、LLM/Geminiへの接続と前工程依存制御を追加。
3. **非同期処理と保存**: Cloud Tasks＆ワーカー経由で画像生成ジョブを処理し、成果物バイナリを GCS/ローカル双方に保存できるようにする。
4. **認証と多ユーザー対応**: Firebase Authentication とローカル代替を導入し、プロジェクト単位のアクセス制御を整備。
5. **デプロイ & 運用準備**: Terraform/Cloud BuildでGCPデプロイを自動化し、モニタリング・コスト管理・ダッシュボードの初期セットを配置する。
