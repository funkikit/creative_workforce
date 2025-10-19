import type { FormEvent } from "react";

import type { ChatEvent, ChatMessage, ChatSession } from "../../lib/types/chat";

type ChatPanelProps = {
  sessions: ChatSession[];
  selectedSessionId: number | null;
  onSelectSession: (sessionId: number) => void;
  onCreateSession: () => void;
  isCreatingSession: boolean;
  messages: ChatMessage[];
  events: ChatEvent[];
  chatInput: string;
  onChatInputChange: (value: string) => void;
  onSendMessage: (event: FormEvent<HTMLFormElement>) => void;
  isSendingMessage: boolean;
  templateLabelMap: Record<string, string>;
};

export function ChatPanel({
  sessions,
  selectedSessionId,
  onSelectSession,
  onCreateSession,
  isCreatingSession,
  messages,
  events,
  chatInput,
  onChatInputChange,
  onSendMessage,
  isSendingMessage,
  templateLabelMap,
}: ChatPanelProps) {
  const selectedSession = sessions.find((session) => session.id === selectedSessionId) ?? null;

  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">会話エージェント</h2>
          <p className="text-sm text-slate-400">チャット経由でエージェントに制作指示を出したり、進捗を確認できます。</p>
        </div>
        <button
          type="button"
          onClick={onCreateSession}
          disabled={isCreatingSession}
          className="rounded-lg border border-blue-500/60 px-4 py-2 text-sm font-semibold text-blue-100 transition hover:border-blue-400 hover:bg-blue-500/10 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
        >
          {isCreatingSession ? "セッション作成中..." : "新しいセッション"}
        </button>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">セッション一覧</h3>
          <div className="space-y-2">
            {sessions.length ? (
              sessions.map((session) => {
                const isActive = session.id === selectedSessionId;
                return (
                  <button
                    key={session.id}
                    type="button"
                    onClick={() => onSelectSession(session.id)}
                    className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition ${
                      isActive
                        ? "border-blue-500/70 bg-blue-500/10 shadow"
                        : "border-slate-800 bg-slate-950/40 hover:border-blue-500/40 hover:bg-blue-500/5"
                    }`}
                  >
                    <span className="block font-semibold text-white">{session.title ?? `セッション #${session.id}`}</span>
                    <span className="mt-1 block text-xs text-slate-400">ステータス: {session.status}</span>
                  </button>
                );
              })
            ) : (
              <p className="rounded-xl border border-dashed border-slate-700 bg-slate-950/30 px-4 py-5 text-sm text-slate-400">
                まだ会話セッションがありません。ボタンから開始してください。
              </p>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
            <h3 className="text-sm font-semibold text-white">メッセージ</h3>
            <div className="mt-3 flex h-64 flex-col gap-3 overflow-y-auto rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 text-sm">
              {selectedSession ? (
                messages.length ? (
                  messages.map((message) => (
                    <div key={message.id} className="space-y-1">
                      <span
                        className={`text-xs font-semibold uppercase tracking-wide ${
                          message.role === "assistant" ? "text-blue-200" : "text-slate-400"
                        }`}
                      >
                        {message.role === "assistant" ? "アシスタント" : "ユーザー"}
                      </span>
                      <p className="whitespace-pre-wrap text-slate-100">{message.content}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-400">まだメッセージがありません。メッセージを送信してください。</p>
                )
              ) : (
                <p className="text-sm text-slate-400">セッションを選択してください。</p>
              )}
            </div>

            <form className="mt-4 space-y-3" onSubmit={onSendMessage}>
              <textarea
                value={chatInput}
                onChange={(event) => onChatInputChange(event.target.value)}
                disabled={!selectedSession || isSendingMessage}
                className="h-24 w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:cursor-not-allowed disabled:text-slate-500"
                placeholder="生成したい成果物や進捗の確認事項を日本語で入力してください"
              />
              <div className="flex items-center justify-end">
                <button
                  type="submit"
                  disabled={!selectedSession || isSendingMessage || !chatInput.trim()}
                  className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:bg-slate-700"
                >
                  {isSendingMessage ? "送信中..." : "メッセージを送信"}
                </button>
              </div>
            </form>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5">
            <h3 className="text-sm font-semibold text-white">イベント</h3>
            <div className="mt-3 space-y-2 text-sm">
              {selectedSession ? (
                events.length ? (
                  events.map((event) => {
                    const payload = event.payload ?? {};
                    let description = JSON.stringify(payload);
                    if (event.type === "status") {
                      const phase = typeof payload.phase === "string" ? payload.phase : String(payload.phase ?? "unknown");
                      const intent = typeof payload.intent === "string" ? payload.intent : "";
                      description = `ステータス: ${phase} ${intent ? `/ intent: ${intent}` : ""}`.trim();
                    }
                    if (event.type === "artifact_update") {
                      const templateCode = typeof payload.template_code === "string" ? payload.template_code : "";
                      const label = templateLabelMap[templateCode] ?? templateCode;
                      const artifactId =
                        typeof payload.artifact_id === "number"
                          ? payload.artifact_id
                          : typeof payload.artifact_id === "string"
                          ? payload.artifact_id
                          : "-";
                      description = `${label || "成果物"} (ID: ${artifactId}) を更新しました`;
                    }
                    return (
                      <div key={event.id} className="rounded-xl border border-slate-800/80 bg-slate-950/70 px-3 py-2">
                        <p className="text-xs text-slate-400">
                          {new Date(event.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </p>
                        <p className="text-slate-100">{description}</p>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-sm text-slate-400">最新イベントはありません。</p>
                )
              ) : (
                <p className="text-sm text-slate-400">セッションを選択してください。</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
