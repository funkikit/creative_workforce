import Image from "next/image";

import type { ArtifactContent } from "../../lib/types/dashboard";

type ArtifactPreviewProps = {
  artifactContent: ArtifactContent | null;
  className?: string;
};

function containerClass(base: string, extra?: string) {
  return extra ? `${base} ${extra}` : base;
}

export function ArtifactPreview({ artifactContent, className }: ArtifactPreviewProps) {
  if (!artifactContent) {
    return (
      <section className={containerClass("rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur", className)}>
        <h2 className="text-lg font-semibold text-white">成果物プレビュー</h2>
        <div className="mt-4 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 p-6 text-sm text-slate-400">
          成果物を選択すると内容を確認できます。
        </div>
      </section>
    );
  }

  if (artifactContent.is_binary && artifactContent.content) {
    const dataUrl = `data:image/png;base64,${artifactContent.content}`;
    return (
      <section className={containerClass("rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur", className)}>
        <h2 className="text-lg font-semibold text-white">成果物プレビュー</h2>
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <p className="text-xs text-slate-400">バイナリアセットのプレビュー</p>
          <div className="relative mt-3 h-80 w-full">
            <Image
              src={dataUrl}
              alt="生成されたキーフレーム"
              fill
              unoptimized
              className="rounded-lg border border-slate-800 object-contain"
              sizes="(max-width: 1024px) 100vw, 640px"
            />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={containerClass("rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur", className)}>
      <h2 className="text-lg font-semibold text-white">成果物プレビュー</h2>
      <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
        <pre className="max-h-80 overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
          {artifactContent.content}
        </pre>
      </div>
    </section>
  );
}
