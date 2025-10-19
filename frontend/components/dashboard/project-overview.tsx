import type { Artifact, Progress, Project } from "../../lib/types/dashboard";

type ProjectOverviewProps = {
  project: Project | null;
  progress: Progress | null;
  artifacts: Artifact[];
};

export function ProjectOverview({ project, progress, artifacts }: ProjectOverviewProps) {
  if (!project) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
        <h2 className="text-lg font-semibold text-white">プロジェクト概要</h2>
        <div className="mt-4 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 p-6 text-sm text-slate-400">
          プロジェクトを選択すると詳細と進捗が表示されます。
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
      <h2 className="text-lg font-semibold text-white">プロジェクト概要</h2>
      <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xl font-semibold text-white">{project.name}</p>
          <p className="mt-1 text-sm text-slate-300">{project.description || "説明が未入力です。"}</p>
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-slate-300">
          <span className="rounded-full border border-slate-700/80 px-3 py-1">予定話数 {project.episodes_planned}</span>
          {progress ? (
            <span className="rounded-full border border-slate-700/80 px-3 py-1">エピソード {progress.episodes.length} 件</span>
          ) : null}
        </div>
      </div>
      {progress ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-4 text-sm">
            <p className="text-xs text-slate-400">グローバル完了</p>
            <p className="mt-2 text-lg font-semibold text-emerald-300">{progress.global.completed.length} 件</p>
          </div>
          <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-4 text-sm">
            <p className="text-xs text-slate-400">グローバル未完了</p>
            <p className="mt-2 text-lg font-semibold text-amber-300">{progress.global.pending.length} 件</p>
          </div>
          <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-4 text-sm">
            <p className="text-xs text-slate-400">総成果物</p>
            <p className="mt-2 text-lg font-semibold text-sky-300">{artifacts.length} 件</p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
