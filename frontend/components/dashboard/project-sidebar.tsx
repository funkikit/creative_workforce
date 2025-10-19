import type { FormEvent } from "react";

import type { Project } from "../../lib/types/dashboard";

export type ProjectFormState = {
  name: string;
  description: string;
  episodes: number;
};

type ProjectSidebarProps = {
  projects: Project[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  projectForm: ProjectFormState;
  onProjectFieldChange: (field: keyof ProjectFormState, value: string | number) => void;
  onCreateProject: (event: FormEvent<HTMLFormElement>) => void;
  className?: string;
};

export function ProjectSidebar({
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  projectForm,
  onProjectFieldChange,
  className,
}: ProjectSidebarProps) {
  return (
    <div className={`space-y-6 ${className ?? ""}`}>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
        <h2 className="text-lg font-semibold text-white">新しいプロジェクト</h2>
        <p className="mt-1 text-xs text-slate-400">
          作品概要と予定話数を入力し、制作ワークスペースを作成します。
        </p>
        <form className="mt-4 space-y-4" onSubmit={onCreateProject}>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-300" htmlFor="project-name">
              名称
            </label>
            <input
              id="project-name"
              required
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              value={projectForm.name}
              onChange={(event) => onProjectFieldChange("name", event.target.value)}
            />
          </div>
          <div>
            <label
              className="text-xs font-semibold uppercase tracking-wide text-slate-300"
              htmlFor="project-description"
            >
              説明
            </label>
            <input
              id="project-description"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              value={projectForm.description}
              onChange={(event) => onProjectFieldChange("description", event.target.value)}
            />
          </div>
          <div>
            <label
              className="text-xs font-semibold uppercase tracking-wide text-slate-300"
              htmlFor="project-episodes"
            >
              予定話数
            </label>
            <input
              id="project-episodes"
              type="number"
              min={1}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              value={projectForm.episodes}
              onChange={(event) => {
                const parsed = Number(event.target.value);
                onProjectFieldChange("episodes", Number.isNaN(parsed) ? 1 : Math.max(1, parsed));
              }}
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:ring-offset-2 focus:ring-offset-slate-950"
          >
            作成
          </button>
        </form>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 backdrop-blur">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">プロジェクト一覧</h2>
          <span className="text-xs text-slate-400">{projects.length} 件</span>
        </div>
        <div className="mt-4 space-y-2">
          {projects.length > 0 ? (
            projects.map((project) => {
              const isSelected = selectedProjectId === project.id;
              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => onSelectProject(project.id)}
                  className={`group w-full rounded-xl border px-4 py-3 text-left transition ${
                    isSelected
                      ? "border-blue-500/70 bg-blue-500/10 shadow"
                      : "border-slate-800 bg-slate-950/50 hover:border-blue-500/40 hover:bg-blue-500/5"
                  }`}
                >
                  <span className="block text-sm font-semibold text-white">{project.name}</span>
                  <span className="mt-1 block text-xs text-slate-400">予定話数: {project.episodes_planned}</span>
                  {project.description ? (
                    <span className="mt-1 block text-xs text-slate-500">{project.description}</span>
                  ) : null}
                </button>
              );
            })
          ) : (
            <p className="rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-5 text-sm text-slate-400">
              まだプロジェクトがありません。上のフォームから作成してください。
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
