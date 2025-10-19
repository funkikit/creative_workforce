import type { Artifact } from "../../lib/types/dashboard";

type ArtifactTableProps = {
  artifacts: Artifact[];
  templateLabelMap: Record<string, string>;
  onSelectArtifact: (artifact: Artifact) => void;
  projectSelected: boolean;
};

export function ArtifactTable({ artifacts, templateLabelMap, onSelectArtifact, projectSelected }: ArtifactTableProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">成果物一覧</h2>
        <span className="text-xs text-slate-400">{artifacts.length} 件</span>
      </div>
      {projectSelected ? (
        artifacts.length > 0 ? (
          <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3 text-left">テンプレート</th>
                  <th className="px-4 py-3 text-left">エピソード</th>
                  <th className="px-4 py-3 text-left">バージョン</th>
                  <th className="px-4 py-3 text-left">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-950/40">
                {artifacts.map((artifact) => {
                  const templateLabel = templateLabelMap[artifact.template_code] ?? artifact.template_code;
                  return (
                    <tr key={artifact.id} className="hover:bg-slate-900/50">
                      <td className="px-4 py-3">
                        <p className="text-sm font-semibold text-white">{templateLabel}</p>
                        <p className="text-xs text-slate-500">{artifact.template_code}</p>
                      </td>
                      <td className="px-4 py-3 text-slate-200">{artifact.episode ?? "-"}</td>
                      <td className="px-4 py-3 text-slate-200">v{artifact.version}</td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          className="rounded-lg border border-slate-700 px-3 py-1 text-xs font-semibold text-slate-100 transition hover:border-blue-500/60 hover:bg-blue-500/10"
                          onClick={() => onSelectArtifact(artifact)}
                        >
                          表示
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-4 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 px-4 py-5 text-sm text-slate-400">
            まだ成果物がありません。テンプレートを選択して生成してください。
          </p>
        )
      ) : (
        <p className="mt-4 text-sm text-slate-400">成果物を操作するプロジェクトを選択してください。</p>
      )}
    </section>
  );
}
