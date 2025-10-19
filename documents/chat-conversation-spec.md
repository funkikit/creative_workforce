# ChatAPI / 会話ルーター と tRPC クライアント設計メモ

更新日: 2024-XX-XX  
作成者: Codex (対話エージェント)

---

## 1. 背景と目的
- 既存 PoC はプロジェクト/成果物 API を中心にしたバッチ的操作に留まっており、ユーザーが自然言語で制作指示を出せる「会話体験」が未整備。
- Mermaid 図に示された ChatAPI・会話ルーティング・tRPC 連携を定義し、LangGraph エージェントの呼び出しを対話型 UX に統合する。
- 本ドキュメントは「まず仕様を固める」段階として、API・データモデル・フロントtRPCクライアントの設計方針をまとめる。
  実装に進む前にレビューを受け、必要に応じて TODO を更新する。

---

## 2. 想定ユーザーフロー
1. ユーザーはフロントエンドのチャットUIで日本語メッセージを送信。
2. フロントは tRPC クライアントを通じて Next.js サーバーハンドラへ RPC。
3. tRPC ハンドラは FastAPI バックエンドの `ChatAPI` へ HTTP(S) リクエスト。
4. `ChatAPI` の会話ルーターが LangGraph ベースの会話エージェントを起動。
   - インテント推論（例: 成果物生成・進行確認・情報取得）。
   - 必要に応じて既存 `ProjectService` / `ArtifactService` / 生成エージェントを呼び出す。
   - ミドルステップで非同期ジョブ（画像生成など）を起票し、進捗イベントを push。
5. 生成結果やステータス更新を会話メッセージとして蓄積し、チャットUIへストリームまたはポーリングで返却。

---

## 3. バックエンド設計

### 3.1 新規モジュール構成（案）
```
backend/app/
  api/chat.py                 # FastAPI router（新規）
  agents/conversation.py      # LangGraph 会話エージェント
  services/conversation.py    # 会話セッション管理、ルーティングロジック
  models/chat.py              # SQLModel 定義（Session / Message / Event）
```

### 3.2 データモデル（SQLModel）
- `ChatSession`
  | フィールド | 型 | 説明 |
  | --- | --- | --- |
  | id | int (PK) | セッションID |
  | project_id | Optional[int] | 紐付くプロジェクト |
  | title | str | 会話タイトル（初回メッセージから生成） |
  | status | Enum("active", "closed", "archived") | セッション状態 |
  | created_at / updated_at | datetime | 監査用 |

- `ChatMessage`
  | フィールド | 型 | 説明 |
  | --- | --- | --- |
  | id | int (PK) |
  | session_id | FK -> ChatSession |
  | role | Enum("user", "assistant", "system") |
  | content | Text | 本文（Markdown 可） |
  | metadata | JSON | インテント、関連成果物ID 等 |
  | created_at | datetime |

- `ChatEvent`
  | フィールド | 型 | 説明 |
  | --- | --- | --- |
  | id | int (PK) |
  | session_id | FK |
  | type | Enum("message", "status", "artifact_update", "task_progress") |
  | payload | JSON | イベントペイロード |
  | created_at | datetime |

> **備考:**  
> 会話ログはメッセージ重視、UI 更新用の granular 情報は `ChatEvent` に積む。  
> 将来のストリーミング対応（SSE/WebSocket）に備え、イベントテーブルを用意しておく。

### 3.3 会話ルーター / エージェントの責務
1. **インテント判定**  
   - ルールベース（キーワード） + LLM による分類を組み合わせる。
   - インテント例: `artifact.generate`, `project.summary`, `task.run_worker`, `smalltalk`.
2. **コンテキスト準備**  
   - プロジェクト説明、直近成果物、進捗統計などを `context` として LangGraph に渡す。
3. **アクション実行**  
   - 既存テキスト/画像エージェント呼び出し。  
   - `TaskQueueService` を用いた遅延ジョブ登録。  
   - ステータス計算 (`ProjectProgressService`) の呼び出し。
4. **レスポンス生成**  
   - 会話メッセージ（自然言語）と、必要なメタデータ（リンク、成果物ID）を構築。
   - 非同期処理がある場合は `ChatEvent` に進捗を記録し、フロントがポーリングで取得できるようにする。

### 3.4 REST API エンドポイント（案）
| メソッド & Path | 説明 | 主なペイロード | レスポンス |
| --- | --- | --- | --- |
| `POST /api/chat/sessions` | 新規会話セッション作成 | `{ project_id?: int, title?: str }` | `ChatSessionRead` |
| `GET /api/chat/sessions` | セッション一覧（ページング） | クエリ: `project_id`, `status` | `List[ChatSessionRead]` |
| `GET /api/chat/sessions/{id}` | セッション詳細 | - | `ChatSessionRead` |
| `GET /api/chat/sessions/{id}/messages` | メッセージ履歴取得 | クエリ: `after`, `limit` | `List[ChatMessageRead]` |
| `POST /api/chat/sessions/{id}/messages` | ユーザーメッセージ送信 | `{ content: str, metadata?: json }` | `ChatMessageRead` + `pending_event_id?` |
| `GET /api/chat/sessions/{id}/events` | イベントポーリング/SSE | クエリ: `after` | `List[ChatEventRead]` または SSE |
| `POST /api/chat/sessions/{id}/actions/{action}` | 明示的アクション実行（オプション） | 例: `action=resume-worker` | アクション結果 |

> SSE/WebSocket は後続拡張。第1フェーズはポーリング（`events`）と同期レスポンスで成立させる。

### 3.5 レスポンススキーマ（抜粋）
```jsonc
// ChatMessageRead
{
  "id": 12,
  "session_id": 3,
  "role": "assistant",
  "content": "キーフレーム画像の生成を開始しました。完了次第お知らせします。",
  "metadata": {
    "intent": "artifact.generate",
    "artifact_id": 45,
    "template_code": "keyframe_image"
  },
  "created_at": "2024-06-01T12:34:56Z"
}

// ChatEventRead (task progress)
{
  "id": 88,
  "type": "task_progress",
  "payload": {
    "task_id": "keyframe-abc123",
    "state": "queued",
    "eta": "2024-06-01T12:40:00Z"
  },
  "created_at": "2024-06-01T12:35:01Z"
}
```

---

## 4. フロントエンド tRPC 設計

### 4.1 アーキテクチャ
- Next.js (App Router) に `trpc` ディレクトリを新設。
- tRPC サーバー（Next API Route or Route Handler）から FastAPI へ HTTP 代理通信。
- クライアント側は React Query ベースで `useMutation`, `useInfiniteQuery` を利用。
- 認証は未導入のため簡易クライアント（将来 Auth 導入時に middleware 拡張）。

### 4.2 ルーター構成（案）
```
src/server/trpc/router/chat.ts
  - createSession
  - listSessions
  - getSession
  - listMessages
  - sendMessage
  - listEvents (polling)

src/server/trpc/router/_app.ts       // メインルーターに chat をマウント
src/lib/trpc/client.ts               // クライアントインスタンス
```

### 4.3 Procedure 仕様

| Procedure | 入力 | 出力 | 備考 |
| --- | --- | --- | --- |
| `chat.createSession` | `{ projectId?: number, title?: string }` | `ChatSession` | FastAPI `POST /api/chat/sessions` |
| `chat.listSessions` | `{ projectId?: number, status?: string }` | `{ items, nextCursor }` | ページング対応 |
| `chat.getSession` | `{ sessionId: number }` | `ChatSession` | - |
| `chat.listMessages` | `{ sessionId: number, cursor?: string }` | `{ items, nextCursor }` | `cursor` は ISO 時刻 or message_id |
| `chat.sendMessage` | `{ sessionId: number, content: string }` | `ChatMessage` | 成功時に `chat.listEvents` のポーリング開始 |
| `chat.listEvents` | `{ sessionId: number, after?: string }` | `ChatEvent[]` | 3〜5秒間隔でポーリング / SSE 導入時はストリーミングに差し替え |

> tRPC の入力/出力スキーマは `zod` で定義し、共通型を `frontend/lib/types/chat.ts` に生成する。

### 4.4 フロント実装観点
- チャットUIコンポーネントで `useInfiniteQuery(chat.listMessages)` を利用して履歴読み込み。
- 送信時は `chat.sendMessage` ミューテーション → 成功後にローカルに楽観追加しつつ `listEvents` ポーリングを走らせる。
- イベントで `artifact_update` や `task_progress` を受信 → トースト表示や成果物プレビューの刷新をトリガー。
- 会話内から成果物詳細ページや生成フォームへリンクできるよう `metadata` を活用。

---

## 5. 実装ステップ提案
1. **DB / モデル追加**  
   - `ChatSession`, `ChatMessage`, `ChatEvent` モデルとマイグレーション。
   - `Project` との関連インデックス整備。
2. **サービス/エージェント実装**  
   - `ConversationService` で CRUD + ルーティング。  
   - LangGraph `ConversationAgent` でインテント検出とアクションマッピング実装。
3. **API ルーター追加**  
   - FastAPI `chat.py` 追加。  
   - バリデーション、エラーメッセージは日本語対応。  
   - pytest で API・インテント分岐・イベント処理をカバー。
4. **tRPC サーバー構築**  
   - Next.js 側に tRPC サーバー基本セットアップ（既存プロジェクトへの影響を最小化）。  
   - `chat` ルーター実装、HTTP クライアント（`fetch`）で FastAPI を呼ぶ。
5. **フロント UI 統合（後続）**  
   - 既存コンソールにチャットパネルを追加。  
   - イベントポーリングによる進捗/成果物更新の結合。  
   - UX 改善（送信中インジケータ、ストリーミング対応など）。

---

## 6. オープン課題・検討事項
- **認証/ユーザー識別**: 現状シングルユーザー想定。将来的に `user_id` 列を追加する想定でスキーマを柔軟に。
- **ストリーミング**: SSE or WebSocket をどのフェーズで導入するか。初期リリースはポーリング。
- **テキスト生成モデル**: `TemplateLLMClient` はダミーのため、OpenAI/Gemini 実運用時のプロンプトや安全対策を別途設計。
- **メッセージ上限**: セッションの長期化でストレージ/コンテキストが膨れ上がる課題。アーカイブ戦略が必要。
- **tRPC と REST 並存**: 既存の直接 `fetch` する画面との共存をどう整理するか（段階的移行 or ハイブリッド）。

---

## 7. 次のアクション
1. 本仕様をチームレビュー（要・不要のフィールド、エンドポイントの粒度など）。
2. `documents/TODO.md` を更新し、仕様策定済みであることと次タスク（実装 & テスト）を追記。
3. レビューで承認を得たら、バックエンド DB モデル/マイグレーション実装に着手する。

---

以上。
