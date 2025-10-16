# PoC仕様書：クリエイティブ制作支援エージェント基盤

## 1. 目的とスコープ
- 作品単位（=プロジェクト）で全体仕様書から各話成果物までを管理し、利用者が対話UIから成果物担当エージェントを呼び出して議論・生成できるPoCを構築する。
- PoCで検証する価値
  - ユーザーが会話内で成果物エージェントを指名し、定型成果物案を生成・修正できる。
  - ユーザー自身がLLMを使わず成果物を編集・アップロードしてもワークフローが破綻しない。
  - 制作進行役が不足資材を把握でき、サイドバーで成果物ディレクトリ構造を一望できる。
  - 絵コンテ（テーブル形式）をもとに画像生成用プロンプトを自動作成し、Gemini 2.5 Flash Image APIで出力画像を提示できる。
- PoCでは工程のマルチプロセス実行や長期運用機能を対象外とし、前工程未完了の成果物にはエージェントが着手しない設計とする。

- ローカル/クラウド切替方針
  - `.env`の `ENV_TARGET` で `local` / `gcp` を切り替え。
  - 抽象化したサービスレイヤー（StorageService, VectorStoreService, TaskQueueService）を用意し、実装をDIする。
  - Docker Compose でローカル依存（PostgreSQL, MinIO, Redis, FastAPI, Next.js）を起動し、クラウド移行時はTerraformなどでGCPリソースを構築。

## 2. システム構成概要
- **ユーザーUI**: Next.js (App Router) + Chakra UI + tRPC。会話UI、成果物ディレクトリサイドバー、制作進行ビュー、成果物編集画面を提供。
  - ローカル: `npm run dev` もしくは Docker Compose。
  - GCP: Cloud Run + Cloud Build。
- **エージェントAPI**: FastAPI + LangGraph。成果物種別ごとに単機能エージェント（全体仕様書、キャラデザ、シナリオ、絵コンテ、原画）を実装。
  - ローカル: Uvicornをローカル起動、もしくはDocker Compose。
  - GCP: Cloud Runでコンテナ運用。
- **LLM/画像生成**: OpenAI GPT-5（主力）、OpenAI o3-mini（補助）、Gemini 2.5 Flash Image API（原画生成）。生成はAPIベースで完結し、プロンプト提示と生成画像プレビューを提供。
  - ローカル: OpenAI/Gemini APIキーを環境変数で指定し、ネットワーク越しに呼び出し。オフライン時はモックアダプタがプレースホルダー画像とプロンプトのみ返す。
  - GCP: Vertex AI経由でGemini APIを呼び出し、成果物に保存。
- **永続化**:
  - Cloud SQL (PostgreSQL) / ローカルPostgreSQL（Docker）。Prisma or SQLModelでマイグレーション共通化。
  - GCS / ローカルMinIO or ローカルディレクトリ。StorageServiceで抽象化。
  - Vertex AI Vector Search / ローカルQdrant。VectorStoreServiceで抽象化。
- **非同期処理**:
  - GCP: Cloud Tasks + Cloud Run Jobs。
  - ローカル: Redis Queue (RQ) or Celery + Redis で代替。TaskQueueServiceで統一。
- **インフラ管理**:
  - ローカル: Docker Compose (`frontend`, `backend`, `db`, `minio`, `redis`).
  - GCP: Cloud Build (CI)、TerraformでCloud Run/SQL/Tasks/Storage等を構築。
- **認証**:
  - GCP: Firebase Authentication (Google Sign-in)。
  - ローカル: 開発用の簡易認証（固定ユーザー、もしくはAuth0/Firebaseのローカルエミュレータ）を提供。

## 3. 成果物テンプレート構成
- プロジェクト（作品）単位成果物
  - `overall_spec`: 全体仕様書（長期シナリオ・キャラ設定・世界観をMarkdownで記録）。
  - `character_design`: キャラクターデザイングリッド（テキスト + 参考画像リンク）。
  - `background_sample`: 背景サンプル画像セット（GCSの画像リスト）。
- 各話成果物（エピソードごとにサブディレクトリ）
  - `episode_summary`: 話数の概要サマリ（Markdown）。
  - `episode_script`: シナリオ本文（Markdown）。
  - `storyboard_table`: タイムテーブル別画面設計案（timecode, board_description, directing_notesのテーブル）。
- `keyframe_image`: 原画画像（Gemini APIで生成またはユーザーアップロード）。
- 成果物は定型テンプレートで流動性が低く、前工程が完了していない場合は後工程エージェントを実行しない。
- サイドバーはこのテンプレート構造をディレクトリ表示し、制作進行ビューは不足テンプレートを一覧化する。

## 4. コンポーネント詳細
### 4.1 フロントエンド
- 会話UI: プロジェクトと成果物の文脈を表示しながらチャット。成果物エージェント呼び出しボタンで対象テンプレートを選択。
- 成果物サイドバー: プロジェクト配下に「全体仕様」「キャラデザ」「背景サンプル」「第1話…」をディレクトリ構造で表示。未作成は強調表示。
- 成果物編集ビュー: 定型テンプレートをフォーム/Markdown/テーブルで編集。ユーザー手動入力とエージェント生成結果を差分表示。ファイルアップロード対応。
- 制作進行ビュー: 必須成果物の充足状況と不足理由（例: 「絵コンテ未作成」）を一覧化。
- 技術ポイント: tRPCでAPI呼び出し、React Queryでサーバーデータ管理、ZustandでUI状態を保持。

### 4.2 バックエンド（FastAPI + LangGraph）
- エンドポイント:
  - `/api/chat`: 会話投稿・履歴・成果物エージェント呼び出し。
  - `/api/artifacts`: 成果物テンプレート一覧、内容取得、生成依頼、手動アップロード、バージョン管理。
  - `/api/progress`: 不足成果物リストと依存関係ステータスを返却。
  - `/api/generation/image`: 絵コンテ成果物から原画生成ジョブを登録。
- LangGraph構成:
  - エージェントは成果物テンプレート単位（`ProjectSpecAgent`, `CharacterDesignAgent`, `EpisodeSummaryAgent`, `ScenarioAgent`, `StoryboardAgent`, `KeyframeAgent`）。
  - 各エージェントは単工程でテンプレートに沿った成果物案を生成し、Cloud SQL/GCSへ保存。
  - 依存成果物が未完了の場合は実行せず、制作進行ビューに不足として登録。
- 非同期ジョブ:
  - Cloud Tasksに原画生成ジョブを登録。
  - Cloud Run Job（またはローカルキューのワーカー）がGemini APIを呼び出し、生成結果を保存。

### 4.3 データスキーマ（初期案）
- `projects`: id, title, synopsis, status, created_at。
- `artifact_templates`: code (`project_spec`, `character_design`, `background_sample`, `episode_summary`, `episode_script`, `storyboard_table`, `keyframe_image`), parent_code, display_name, storage_type(enum: markdown/table/image), schema_definition(jsonb)。
- `artifacts`: id, project_id, template_code, version, status(enum: draft/final), storage_path, created_by, created_at, updated_at。
- `artifact_dependencies`: template_code, depends_on, optional(boolean)。
- `messages`: id, project_id, artifact_id nullable, role(enum: user/agent/system), content, created_at。
- `agents`: code, template_code, name, description, llm_model。
- `generation_jobs`: id, artifact_id, engine(enum: gemini/comfyui), payload(jsonb), status(enum: pending/running/succeeded/failed), output_path, created_at。
- `missing_assets_view`: `artifact_templates`と`artifacts`を突合して不足成果物を抽出するSQLビュー。

### 4.4 画像生成フロー（絵コンテ → 原画）
1. ユーザーまたはエージェントが「タイムテーブル別画面設計案（絵コンテ）」成果物を完成（timecode / board_description / directing_notes列）。
2. `KeyframeAgent`を呼び出し、対象カットを指定。エージェントがGemini向けプロンプトと付随画像参照（あれば）を生成。
3. FastAPIが依存関係を確認し、`generation_jobs`に登録、Cloud Tasks（またはローカルキュー）へ投入。
4. ジョブがGemini 2.5 Flash Image APIを呼び出し、生成画像と使用プロンプトをGCS（またはローカルストレージ）へ保存。
5. 完了通知を会話UIに送信し、成果物サイドバーと制作進行ビューを更新。ユーザーは生成プロンプトと画像を確認し必要に応じて再生成/外部活用できる。

## 5. 実装フェーズとタスク
### フェーズA: 基盤セットアップ（2週間）
- GCPプロジェクト作成、IAM/サービスアカウント設定、Cloud Run/Cloud SQL/Vertex AI/Cloud Tasks/Cloud Buildの有効化。
- Cloud SQLスキーマ（プロジェクト・成果物・テンプレート）とGCSバケット構成を整備。
- FastAPI + LangGraphの骨格実装、GPT-5 API接続、成果物テンプレート定義APIを実装。
- Next.jsで会話UIと成果物サイドバーのプロトタイプを構築。
- Docker Composeを整備し、ローカル向けPostgreSQL/MinIO/Redis構成を起動可能にする。

### フェーズB: 成果物エージェント・制作進行統合（3週間）
- 成果物編集ビュー、手動アップロード機能、制作進行ビューの実装。
- 成果物エージェント（全体仕様書〜シナリオ〜絵コンテ）をLangGraphで実装し依存管理を組み込み。
- Cloud Tasks + Cloud Run JobsでGemini 2.5 Flash Image API連携を実装し、原画生成フローとプロンプト提示UIを整備。
- Vertex AI Vector Searchを用いた全体仕様書・過去成果物の参照機能を会話UIに組み込み。

### フェーズC: 画像生成チューニングとユーザーテスト（2週間）
- 原画生成UIでプロンプト編集・再生成のパラメータ（スタイル、サイズ、バリエーション数）を調整可能にする。
- 生成プロンプトと結果画像を履歴として保存し、ユーザーが外部ツールに持ち出せるダウンロード機能を実装。
- 内部ユーザー向けテスト（ユーザー/制作進行/エージェント利用）を実施しフィードバック反映。

## 6. 提供機能一覧（PoC完成時）
- **会話型エージェント呼び出し**: GPT-5と対話しながら成果物エージェント（全体仕様書/シナリオ/絵コンテ/原画など）を指名し、定型成果物案を生成・修正。
- **成果物ディレクトリ表示**: サイドバーにプロジェクト配下の成果物をディレクトリ構造で表示。未作成・要更新のアイテムをハイライト。
- **成果物編集とアップロード**: テンプレートに沿ったフォーム・Markdown・テーブル編集、手動アップロード、バージョン履歴管理。
- **制作進行ビュー**: 必須成果物の充足状況、不足理由、依存関係を一覧化。原画エージェントへ進めない理由を可視化。
- **画像合成**: 絵コンテからGemini 2.5 Flash Image APIを呼び出し、生成プロンプトと画像を提供。履歴管理と外部ツール向けダウンロードをサポート。
- **知識参照**: 全体仕様書や過去成果物をEmbeddingで検索し、会話内から引用。
- **設定管理**: APIキー、Geminiエンドポイント、ローカル/クラウド切替を設定画面と構成ファイルで管理し環境差異を吸収。

## 7. 非機能要件（PoC水準）
- **可用性**: Cloud Runの最小構成で99%稼働を目指す。重要ジョブは最大1回リトライ。
- **セキュリティ**: IAMロールにより各サービスを分離。APIキー等はSecret Managerで保管。
- **ログ/監視**: Cloud Logging + Error Reportingのみを利用。詳細なメトリクスは次フェーズ。
- **コスト**: 月間利用を500ドル以下に収める想定（GPT-5トークン費 + Gemini APIを中心に試算。GPU費用は発生しない想定）。
- **工程順守**: 成果物エージェントは依存テンプレートが揃った場合にのみ起動し、並列実行による競合を避ける。

## 8. 成果物
- PoC環境（GCP）で動作するWebアプリとAPI。
- 技術メモ（この仕様書、運用手順書、プロンプトテンプレート集）。
- ユーザーテストレポート（操作性・生成品質・改善要望）。

## 9. リスクと対応
- **APIコスト変動**: トライアル期間で呼び出し上限を設け、コストモニターをダッシュボード化。
- **Geminiモデル制約**: 品質が要件を満たさない場合に備え、プロンプト調整機能と外部ツールへの持ち出し（生成プロンプト/画像のダウンロード）で代替案を提供。

## 10. 今後の拡張検討項目
- Temporal等の高度ワークフロー導入、Blender自動化フロー、音響生成（ElevenLabs）との統合。
- 監視・アラート基盤（Cloud Monitoring, OpenTelemetry）拡張。
- 権限管理（ロール別機能制御）、外部クリエイターとの共同編集機能。
