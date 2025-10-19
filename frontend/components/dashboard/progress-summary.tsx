import type { Progress } from "../../lib/types/dashboard";

type ProgressSummaryProps = {
  progress: Progress | null;
  templateLabelMap: Record<string, string>;
};

export function ProgressSummary({ progress, templateLabelMap }: ProgressSummaryProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
      <h2 className="text-lg font-semibold text-white">進捗サマリー</h2>
      {progress ? (
        <div className="mt-4 space-y-5 text-sm">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-300">グローバルテンプレート</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {progress.global.completed.length ? (
                progress.global.completed.map((code) => (
                  <span
                    key={`global-completed-${code}`}
                    className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-200"
                  >
                    完了: {templateLabelMap[code] ?? code}
                  </span>
                ))
              ) : (
                <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
                  完了したテンプレートはありません
                </span>
              )}
              {progress.global.pending.length
                ? progress.global.pending.map((code) => (
                    <span
                      key={`global-pending-${code}`}
                      className="rounded-full bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-200"
                    >
                      未完了: {templateLabelMap[code] ?? code}
                    </span>
                  ))
                : null}
            </div>
          </div>

          <div className="space-y-3">
            {progress.episodes.map((episodeState) => (
              <div key={episodeState.episode} className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4">
                <h4 className="text-sm font-semibold text-white">エピソード {episodeState.episode}</h4>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  {episodeState.completed.length ? (
                    episodeState.completed.map((code) => (
                      <span
                        key={`episode-${episodeState.episode}-completed-${code}`}
                        className="rounded-full bg-emerald-500/15 px-3 py-1 font-semibold text-emerald-200"
                      >
                        完了: {templateLabelMap[code] ?? code}
                      </span>
                    ))
                  ) : (
                    <span className="rounded-full border border-slate-700 px-3 py-1 text-slate-400">完了なし</span>
                  )}
                  {episodeState.pending.map((code) => (
                    <span
                      key={`episode-${episodeState.episode}-pending-${code}`}
                      className="rounded-full bg-amber-500/15 px-3 py-1 font-semibold text-amber-200"
                    >
                      未完了: {templateLabelMap[code] ?? code}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-400">進捗を確認するにはプロジェクトを選択してください。</p>
      )}
    </section>
  );
}
