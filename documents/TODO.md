# TODO Roadmap (キャッチアップ対象: `documents/creative-workforce-system-spec.md`)

## 完了済みアップデート
- [x] `creative_workforce-system-spec.md` でバックエンド・フロントエンド・インフラ仕様を統合し、旧仕様書を整理。
- [x] Next.js フロントを Tailwind ベースの `AppShell` レイアウトへ刷新し、サイドバー/ヒーロー/チャットパネルをコンポーネント化。
- [x] `postcss.config.js` / `tailwind.config.ts` を追加し、デザイン共通トークンを導入。
- [x] tRPC チャット機能・成果物生成フローをモダンUIに組み込み、成果物プレビューを `next/image` で最適化。

## 進行中／優先タスク
- [ ] **会話体験の強化**  
  - ストリーミング、意図確認、イベントログの追従表示を追加。  
  - 既存 `ChatPanel` にトースト/タイムライン UI を差し込む。
- [ ] **API レイヤーのモジュール化**  
  - `frontend/lib/api-client` を整備し、fetch エラーハンドリング・ローディング管理を統一。  
  - `useProjectDashboard` 的な複合フックでデータフェッチ責務を集約。
- [ ] **成果物メタ情報の解像度向上**  
  - バックエンド API で `artifact` の `updated_at`, `author` を返却し、UI へ表示。  
  - 進捗サマリーに完了日時と担当者バッジを追加。
- [ ] **CI/CD 強化**  
  - Terraform/Cloud Build の IaC 整備と GitHub Actions からのデプロイトリガーを実装。  
  - `pnpm test` が空振りしないようサンプルテストを拡張し、モックを導入。

## 次に着手したい検討事項
1. **認証とアクセス制御**  
   - Firebase/Auth0 との連携方針確定、PoC 向け簡易ログインの提供。
2. **成果物編集とレビュー導線**  
   - Markdown プレビューや差分表示を検討し、エディタコンポーネントを選定。
3. **モニタリング・コスト管理**  
   - Gemini/LLM 呼び出しのコストガード、Cloud Logging / BigQuery へのイベント送信。
4. **ユーザーテストとUX計測**  
   - コンソール操作のヒートマップ/イベントログ設計。Figma プロトタイプと合わせてユーザー調査を実施。

## メモ
- 旧仕様書（`PoC仕様書.md`, `ディレクトリとアーキテクチャ案.md`, `frontend-uiux-plan.md` など）は統合ドキュメントに移行済み。最新仕様は `creative_workforce-system-spec.md` を参照。
- docs 配下は **仕様書 / ガイド / 提案資料** の３カテゴリで整理。新規ドキュメント作成時は README に追記すること。
