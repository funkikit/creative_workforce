import type { ChangeEvent } from "react";

import type { GenerationTemplate } from "../../lib/types/dashboard";

type PendingKeyframeTask = {
  projectId: number;
  episode: number | null;
  instructions: string;
  createdBy: string;
} | null;

type GenerationPanelProps = {
  templates: GenerationTemplate[];
  instructions: string;
  onInstructionsChange: (value: string) => void;
  episode: number | "";
  onEpisodeChange: (value: number | "") => void;
  onGenerate: (template: GenerationTemplate) => void;
  disabled: boolean;
  pendingKeyframe: PendingKeyframeTask;
  onProcessKeyframe: () => void;
  requiresProjectSelection: boolean;
};

export function GenerationPanel({
  templates,
  instructions,
  onInstructionsChange,
  episode,
  onEpisodeChange,
  onGenerate,
  disabled,
  pendingKeyframe,
  onProcessKeyframe,
  requiresProjectSelection,
}: GenerationPanelProps) {
  const handleEpisodeChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.value === "") {
      onEpisodeChange("");
      return;
    }
    const next = Number(event.target.value);
    onEpisodeChange(Number.isNaN(next) ? "" : Math.max(1, next));
  };

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">成果物を生成</h2>
          <p className="text-sm text-slate-400">テンプレートを選択して LLM / 画像ワーカーに生成を依頼します。</p>
        </div>
        {requiresProjectSelection ? (
          <span className="rounded-full border border-amber-500/50 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200">
            先にプロジェクトを選択してください
          </span>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-[220px_auto]">
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-300" htmlFor="episode-input">
              エピソード番号（任意）
            </label>
            <input
              id="episode-input"
              type="number"
              min={1}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              value={episode}
              onChange={handleEpisodeChange}
            />
          </div>
          {pendingKeyframe ? (
            <div className="rounded-xl border border-amber-400/50 bg-amber-500/10 p-4 text-xs text-amber-100">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">キーフレーム生成タスクが保留中です。</p>
                  <p className="mt-1">ワーカーを実行してシミュレーションを完了させてください。</p>
                </div>
                <button
                  type="button"
                  className="rounded-lg bg-amber-400 px-3 py-1 text-xs font-semibold text-amber-900 transition hover:bg-amber-300"
                  onClick={onProcessKeyframe}
                >
                  ワーカーを実行
                </button>
              </div>
            </div>
          ) : null}
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-300" htmlFor="generation-instructions">
            生成指示
          </label>
          <textarea
            id="generation-instructions"
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-3 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            value={instructions}
            onChange={(event) => onInstructionsChange(event.target.value)}
            rows={5}
          />
          <p className="mt-2 text-xs text-slate-400">生成物に反映したいニュアンスや修正ポイントを日本語で記述できます。</p>
        </div>
      </div>

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-300">テンプレート一覧</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {templates.map((template) => (
            <button
              key={template.code}
              type="button"
              disabled={disabled}
              onClick={() => onGenerate(template)}
              className={`group rounded-xl border px-4 py-3 text-left text-sm transition ${
                disabled
                  ? "cursor-not-allowed border-slate-800 bg-slate-950/40 text-slate-500"
                  : "border-slate-800 bg-slate-950/50 hover:border-blue-500/60 hover:bg-blue-500/10"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="block text-base font-semibold text-white">{template.label}</span>
                  <span className="mt-1 block text-xs text-slate-400">
                    コード: {template.code}
                    {template.requiresEpisode ? "（エピソード指定）" : ""}
                  </span>
                </div>
                <span
                  aria-hidden
                  className="mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full border border-blue-500/50 text-xs font-semibold text-blue-300 transition group-hover:border-blue-300 group-hover:text-blue-100"
                >
                  ▶
                </span>
              </div>
              <span className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-blue-300 group-hover:text-blue-100">
                生成する
              </span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
