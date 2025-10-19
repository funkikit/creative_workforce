"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";

import { trpc } from "../lib/trpc/client";
import type { ChatEvent, ChatMessage, ChatSession } from "../lib/types/chat";

type Project = {
  id: number;
  name: string;
  description?: string | null;
  episodes_planned: number;
};

type Artifact = {
  id: number;
  template_code: string;
  episode?: number | null;
  version: number;
  storage_path: string;
  status: string;
  created_by: string;
  created_at: string;
};

type Progress = {
  global: { completed: string[]; pending: string[] };
  episodes: Array<{ episode: number; completed: string[]; pending: string[] }>;
};

type ArtifactContent = {
  artifact: Artifact;
  content: string | null;
  content_type: string;
  is_binary: boolean;
};

type GenerationTemplate = {
  code: string;
  label: string;
  kind: "text" | "image";
  requiresEpisode?: boolean;
};


const TEMPLATES: GenerationTemplate[] = [
  { code: "overall_spec", label: "作品全体仕様書", kind: "text" },
  { code: "character_design", label: "キャラクター設定", kind: "text", requiresEpisode: true },
  { code: "background_sample", label: "背景サンプル", kind: "text" },
  { code: "episode_summary", label: "エピソード概要", kind: "text", requiresEpisode: true },
  { code: "episode_script", label: "エピソード脚本", kind: "text", requiresEpisode: true },
  { code: "storyboard_table", label: "絵コンテ表", kind: "text", requiresEpisode: true },
  { code: "keyframe_image", label: "キーフレーム画像", kind: "image", requiresEpisode: true },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [projectForm, setProjectForm] = useState({ name: "", description: "", episodes: 1 });
  const [instructions, setInstructions] = useState(
    "作品世界の概要と雰囲気が伝わる説明を日本語で作成してください。"
  );
  const [episode, setEpisode] = useState<number | "">(1);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedArtifactContent, setSelectedArtifactContent] = useState<ArtifactContent | null>(null);
  const [pendingKeyframe, setPendingKeyframe] = useState<null | {
    projectId: number;
    episode: number | null;
    instructions: string;
    createdBy: string;
  }>(null);
  const [selectedChatSessionId, setSelectedChatSessionId] = useState<number | null>(null);
  const [chatInput, setChatInput] = useState("質問や指示をどうぞ。");

  const trpcUtils = trpc.useUtils();

  const chatSessionsQuery = trpc.chat.listSessions.useQuery({});
  const chatCreateSession = trpc.chat.createSession.useMutation({
    onSuccess: (session) => {
      void trpcUtils.chat.listSessions.invalidate();
      setSelectedChatSessionId(session.id);
    },
  });
  const chatMessagesQuery = trpc.chat.listMessages.useQuery(
    selectedChatSessionId ? { sessionId: selectedChatSessionId, limit: 50 } : undefined,
    {
      enabled: selectedChatSessionId !== null,
      refetchInterval: 4000,
    },
  );
  const chatEventsQuery = trpc.chat.listEvents.useQuery(
    selectedChatSessionId ? { sessionId: selectedChatSessionId, limit: 25 } : undefined,
    {
      enabled: selectedChatSessionId !== null,
      refetchInterval: 5000,
    },
  );
  const chatSendMessage = trpc.chat.sendMessage.useMutation({
    onSuccess: () => {
      if (selectedChatSessionId) {
        void trpcUtils.chat.listMessages.invalidate({ sessionId: selectedChatSessionId, limit: 50 });
        void trpcUtils.chat.listEvents.invalidate({ sessionId: selectedChatSessionId, limit: 25 });
      }
      setChatInput("");
    }
  });

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );

  const chatSessions = chatSessionsQuery.data?.items ?? [];
  const selectedChatSession = useMemo(() => {
    if (selectedChatSessionId == null) {
      return null;
    }
    return chatSessions.find((session) => session.id === selectedChatSessionId) ?? null;
  }, [chatSessions, selectedChatSessionId]);

  useEffect(() => {
    if (selectedChatSessionId == null && chatSessions.length > 0) {
      setSelectedChatSessionId(chatSessions[0].id);
    }
  }, [chatSessions, selectedChatSessionId]);

  const chatMessages = chatMessagesQuery.data?.items ?? [];
  const chatEvents = chatEventsQuery.data?.items ?? [];
  const isCreatingSession = chatCreateSession.isPending;
  const isSendingMessage = chatSendMessage.isPending;

  useEffect(() => {
    void loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId != null) {
      void Promise.all([loadArtifacts(selectedProjectId), loadProgress(selectedProjectId)]);
    }
  }, [selectedProjectId]);

  async function loadProjects() {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      if (!response.ok) throw new Error("プロジェクト一覧の取得に失敗しました");
      const data: Project[] = await response.json();
      setProjects(data);
      if (data.length && selectedProjectId == null) {
        setSelectedProjectId(data[0].id);
      }
    } catch (error) {
      console.error(error);
      setMessage("プロジェクト一覧の取得に失敗しました。バックエンドがポート8000で起動しているか確認してください。");
    }
  }

  async function loadArtifacts(projectId: number) {
    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}/artifacts`);
      if (!response.ok) throw new Error("成果物の取得に失敗しました");
      const data: Artifact[] = await response.json();
      setArtifacts(data);
    } catch (error) {
      console.error(error);
      setMessage("成果物の取得に失敗しました");
    }
  }

  async function loadProgress(projectId: number) {
    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}/progress`);
      if (!response.ok) throw new Error("進捗情報の取得に失敗しました");
      const data: Progress = await response.json();
      setProgress(data);
    } catch (error) {
      console.error(error);
      setMessage("進捗情報の取得に失敗しました");
    }
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    try {
      const body = {
        name: projectForm.name,
        description: projectForm.description,
        episodes_planned: projectForm.episodes,
      };
      const response = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error("プロジェクトの作成に失敗しました");
      setProjectForm({ name: "", description: "", episodes: 1 });
      setMessage("プロジェクトを作成しました。");
      await loadProjects();
    } catch (error) {
      console.error(error);
      setMessage("プロジェクトの作成に失敗しました。");
    }
  }

  async function handleGenerate(template: GenerationTemplate) {
    if (!selectedProject) return;
    setLoading(true);
    setMessage(null);
    try {
      const body: Record<string, unknown> = {
        instructions,
        created_by: "demo-user",
      };
      if (template.requiresEpisode && episode !== "") {
        body.episode = Number(episode);
      }

      const response = await fetch(
        `${API_BASE}/projects/${selectedProject.id}/artifacts/${template.code}/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (response.status === 202) {
        setPendingKeyframe({
          projectId: selectedProject.id,
          episode: episode === "" ? null : Number(episode),
          instructions,
          createdBy: "demo-user",
        });
        setMessage("キーフレーム生成タスクをキューに追加しました。ワーカーの実行が必要です。");
      } else if (response.ok) {
        setMessage("成果物を生成しました。");
        await loadArtifacts(selectedProject.id);
      } else {
        const text = await response.text();
        throw new Error(text || "成果物の生成に失敗しました");
      }
    } catch (error) {
      console.error(error);
      setMessage("成果物の生成に失敗しました。");
    } finally {
      setLoading(false);
    }
  }

  async function handleViewArtifact(artifact: Artifact) {
    if (!selectedProject) return;
    setMessage(null);
    try {
      const response = await fetch(
        `${API_BASE}/projects/${selectedProject.id}/artifacts/${artifact.id}`
      );
      if (!response.ok) throw new Error("成果物の内容取得に失敗しました");
      const data: ArtifactContent = await response.json();
      setSelectedArtifactContent(data);
    } catch (error) {
      console.error(error);
      setMessage("成果物の内容取得に失敗しました。");
    }
  }

  async function handleProcessKeyframe() {
    if (!pendingKeyframe || !selectedProject) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE}/tasks/generate-keyframe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: "generate_keyframe",
          project_id: pendingKeyframe.projectId,
          template_code: "keyframe_image",
          episode: pendingKeyframe.episode,
          instructions: pendingKeyframe.instructions,
          created_by: pendingKeyframe.createdBy,
        }),
      });
      if (!response.ok) throw new Error("ワーカー処理に失敗しました");
      setPendingKeyframe(null);
      setMessage("ワーカーがキーフレームを生成しました。");
      await loadArtifacts(selectedProject.id);
    } catch (error) {
      console.error(error);
      setMessage("キーフレーム生成タスクの処理に失敗しました。");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateChatSession() {
    try {
      await chatCreateSession.mutateAsync({
        projectId: selectedProject?.id ?? undefined,
        title: selectedProject ? `${selectedProject.name} セッション` : undefined,
      });
    } catch (error) {
      console.error(error);
      setMessage("会話セッションの作成に失敗しました。");
    }
  }

  async function handleSendChatMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedChatSessionId || !chatInput.trim()) {
      return;
    }

    try {
      await chatSendMessage.mutateAsync({
        sessionId: selectedChatSessionId,
        content: chatInput.trim(),
      });
    } catch (error) {
      console.error(error);
      setMessage("メッセージの送信に失敗しました。");
    }
  }

  function renderArtifactContent() {
    if (!selectedArtifactContent) {
      return (
        <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/40 p-6 text-sm text-slate-400">
          成果物を選択すると内容を確認できます。
        </div>
      );
    }

    if (selectedArtifactContent.is_binary && selectedArtifactContent.content) {
      const dataUrl = `data:image/png;base64,${selectedArtifactContent.content}`;
      return (
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <p className="text-xs text-slate-400">バイナリアセットのプレビュー</p>
          <img
            src={dataUrl}
            alt="生成されたキーフレーム"
            className="mt-3 w-full max-h-80 rounded-lg border border-slate-800 object-contain"
          />
        </div>
      );
    }

    return (
      <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
        <pre className="max-h-80 overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
          {selectedArtifactContent.content}
        </pre>
      </div>
    );
  }

  const selectedProjectName = selectedProject?.name ?? null;

  const pendingTemplateCount = useMemo(() => {
    if (!progress) {
      return null;
    }
    const episodePending = progress.episodes.reduce(
      (accumulator, episodeState) => accumulator + episodeState.pending.length,
      0
    );
    return progress.global.pending.length + episodePending;
  }, [progress]);

  const templateLabelMap = useMemo(() => {
    return TEMPLATES.reduce<Record<string, string>>((map, template) => {
      map[template.code] = template.label;
      return map;
    }, {});
  }, []);

  const stats = useMemo(
    () => [
      {
        label: "登録プロジェクト",
        value: projects.length.toString(),
        helper: projects.length ? "管理中" : "まずは作成",
      },
      {
        label: "生成済み成果物",
        value: artifacts.length.toString(),
        helper: selectedProjectName ? `${selectedProjectName} のデータ` : "プロジェクトを選択",
      },
      {
        label: "未完了テンプレート",
        value: pendingTemplateCount !== null ? `${pendingTemplateCount}件` : "-",
        helper: progress ? "残タスクを確認" : "進捗読み込み待ち",
      },
    ],
    [projects.length, artifacts.length, pendingTemplateCount, progress, selectedProjectName],
  );

  const generationDisabled = !selectedProject || loading;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="relative overflow-hidden border-b border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-black">
        <div className="pointer-events-none absolute -left-10 top-16 h-64 w-64 rounded-full bg-blue-500/20 blur-3xl" />
        <div className="pointer-events-none absolute right-[-6rem] top-32 h-80 w-80 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-6 py-16">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">
            Creative Workforce
          </p>
          <div className="max-w-3xl space-y-3">
            <h1 className="text-3xl font-bold leading-tight sm:text-4xl">
              コンソールで制作フローをオーガナイズ
            </h1>
            <p className="text-sm text-slate-300 sm:text-base">
              プロジェクトの登録から成果物生成、ワーカー処理までをひとつの画面で把握し、PoC の検証をスムーズに進めましょう。
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-slate-800/60 bg-slate-900/40 p-4 shadow-sm backdrop-blur"
              >
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  {stat.label}
                </p>
                <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
                <p className="text-xs text-slate-400">{stat.helper}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mx-auto -mt-10 w-full max-w-7xl px-6 pb-16">
        {message && (
          <div className="mb-6 rounded-2xl border border-blue-500/40 bg-blue-500/10 px-5 py-4 text-sm text-blue-100 backdrop-blur">
            {message}
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
          <aside className="space-y-6">
            <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 backdrop-blur">
              <h2 className="text-lg font-semibold text-white">新しいプロジェクト</h2>
              <p className="mt-1 text-xs text-slate-400">
                作品概要と予定話数を入力し、制作ワークスペースを作成します。
              </p>
              <form className="mt-4 space-y-4" onSubmit={handleCreateProject}>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                    名称
                  </label>
                  <input
                    required
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                    value={projectForm.name}
                    onChange={(event) =>
                      setProjectForm((prev) => ({ ...prev, name: event.target.value }))
                    }
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                    説明
                  </label>
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                    value={projectForm.description}
                    onChange={(event) =>
                      setProjectForm((prev) => ({ ...prev, description: event.target.value }))
                    }
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                    予定話数
                  </label>
                  <input
                    type="number"
                    min={1}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                    value={projectForm.episodes}
                    onChange={(event) =>
                      setProjectForm((prev) => ({ ...prev, episodes: Number(event.target.value) }))
                    }
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
                        onClick={() => setSelectedProjectId(project.id)}
                        className={`group w-full rounded-xl border px-4 py-3 text-left transition ${
                          isSelected
                            ? "border-blue-500/70 bg-blue-500/10 shadow"
                            : "border-slate-800 bg-slate-950/50 hover:border-blue-500/40 hover:bg-blue-500/5"
                        }`}
                      >
                        <span className="block text-sm font-semibold text-white">{project.name}</span>
                        <span className="mt-1 block text-xs text-slate-400">
                          予定話数: {project.episodes_planned}
                        </span>
                        {project.description && (
                          <span className="mt-1 block text-xs text-slate-500">
                            {project.description}
                          </span>
                        )}
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
          </aside>

          <div className="space-y-6">
            <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
              <h2 className="text-lg font-semibold text-white">プロジェクト概要</h2>
              {selectedProject ? (
                <>
                  <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xl font-semibold text-white">{selectedProject.name}</p>
                      <p className="mt-1 text-sm text-slate-300">
                        {selectedProject.description || "説明が未入力です。"}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-3 text-xs text-slate-300">
                      <span className="rounded-full border border-slate-700/80 px-3 py-1">
                        予定話数 {selectedProject.episodes_planned}
                      </span>
                      {progress && (
                        <span className="rounded-full border border-slate-700/80 px-3 py-1">
                          エピソード {progress.episodes.length} 件
                        </span>
                      )}
                    </div>
                  </div>
                  {progress && (
                    <div className="mt-4 grid gap-3 sm:grid-cols-3">
                      <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-4 text-sm">
                        <p className="text-xs text-slate-400">グローバル完了</p>
                        <p className="mt-2 text-lg font-semibold text-emerald-300">
                          {progress.global.completed.length} 件
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-4 text-sm">
                        <p className="text-xs text-slate-400">グローバル未完了</p>
                        <p className="mt-2 text-lg font-semibold text-amber-300">
                          {progress.global.pending.length} 件
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-800/80 bg-slate-950/50 p-4 text-sm">
                        <p className="text-xs text-slate-400">総成果物</p>
                        <p className="mt-2 text-lg font-semibold text-sky-300">
                          {artifacts.length} 件
                        </p>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="mt-4 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 p-6 text-sm text-slate-400">
                  プロジェクトを選択すると詳細と進捗が表示されます。
                </div>
              )}
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">成果物を生成</h2>
                  <p className="text-sm text-slate-400">
                    テンプレートを選択して LLM / 画像ワーカーに生成を依頼します。
                  </p>
                </div>
                {!selectedProject && (
                  <span className="rounded-full border border-amber-500/50 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200">
                    先にプロジェクトを選択してください
                  </span>
                )}
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-[220px_auto]">
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                      エピソード番号（任意）
                    </label>
                    <input
                      type="number"
                      min={1}
                      className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                      value={episode}
                      onChange={(event) =>
                        setEpisode(event.target.value === "" ? "" : Number(event.target.value))
                      }
                    />
                  </div>
                  {pendingKeyframe && (
                    <div className="rounded-xl border border-amber-400/50 bg-amber-500/10 p-4 text-xs text-amber-100">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold">キーフレーム生成タスクが保留中です。</p>
                          <p className="mt-1">
                            ワーカーを実行してシミュレーションを完了させてください。
                          </p>
                        </div>
                        <button
                          type="button"
                          className="rounded-lg bg-amber-400 px-3 py-1 text-xs font-semibold text-amber-900 transition hover:bg-amber-300"
                          onClick={() => void handleProcessKeyframe()}
                        >
                          ワーカーを実行
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                    生成指示
                  </label>
                  <textarea
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-3 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                    value={instructions}
                    onChange={(event) => setInstructions(event.target.value)}
                    rows={5}
                  />
                  <p className="mt-2 text-xs text-slate-400">
                    生成物に反映したいニュアンスや修正ポイントを日本語で記述できます。
                  </p>
                </div>
              </div>

              <div className="mt-6">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                  テンプレート一覧
                </p>
                <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {TEMPLATES.map((template) => (
                    <button
                      key={template.code}
                      type="button"
                      disabled={generationDisabled}
                      onClick={() => void handleGenerate(template)}
                      className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
                        generationDisabled
                          ? "cursor-not-allowed border-slate-800 bg-slate-950/40 text-slate-500"
                          : "border-slate-800 bg-slate-950/50 hover:border-blue-500/50 hover:bg-blue-500/10"
                      }`}
                    >
                      <span className="block text-base font-semibold text-white">
                        {template.label}
                      </span>
                      <span className="mt-1 block text-xs text-slate-400">
                        コード: {template.code}
                        {template.requiresEpisode ? "（エピソード指定）" : ""}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
              <div className="space-y-6">
                <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-white">成果物一覧</h2>
                    <span className="text-xs text-slate-400">{artifacts.length} 件</span>
                  </div>
                  {selectedProject ? (
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
                              const templateLabel =
                                templateLabelMap[artifact.template_code] ?? artifact.template_code;
                              return (
                                <tr key={artifact.id} className="hover:bg-slate-900/50">
                                  <td className="px-4 py-3">
                                    <p className="text-sm font-semibold text-white">{templateLabel}</p>
                                    <p className="text-xs text-slate-500">{artifact.template_code}</p>
                                  </td>
                                  <td className="px-4 py-3 text-slate-200">
                                    {artifact.episode ?? "-"}
                                  </td>
                                  <td className="px-4 py-3 text-slate-200">v{artifact.version}</td>
                                  <td className="px-4 py-3">
                                    <button
                                      type="button"
                                      className="rounded-lg border border-slate-700 px-3 py-1 text-xs font-semibold text-slate-100 transition hover:border-blue-500/60 hover:bg-blue-500/10"
                                      onClick={() => void handleViewArtifact(artifact)}
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
                    <p className="mt-4 text-sm text-slate-400">
                      成果物を操作するプロジェクトを選択してください。
                    </p>
                  )}
                </section>

                <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
                  <h2 className="text-lg font-semibold text-white">進捗サマリー</h2>
                  {progress ? (
                    <div className="mt-4 space-y-5 text-sm">
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                          グローバルテンプレート
                        </h3>
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
                          {progress.global.pending.length ? (
                            progress.global.pending.map((code) => (
                              <span
                                key={`global-pending-${code}`}
                                className="rounded-full bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-200"
                              >
                                未完了: {templateLabelMap[code] ?? code}
                              </span>
                            ))
                          ) : null}
                        </div>
                      </div>

                      <div className="space-y-3">
                        {progress.episodes.map((episodeState) => (
                          <div
                            key={episodeState.episode}
                            className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-4"
                          >
                            <h4 className="text-sm font-semibold text-white">
                              エピソード {episodeState.episode}
                            </h4>
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
                                <span className="rounded-full border border-slate-700 px-3 py-1 text-slate-400">
                                  完了なし
                                </span>
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
                    <p className="mt-4 text-sm text-slate-400">
                      進捗を確認するにはプロジェクトを選択してください。
                    </p>
                  )}
                </section>
              </div>

              <section className="hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur xl:block">
                <h2 className="text-lg font-semibold text-white">成果物プレビュー</h2>
                <div className="mt-4">{renderArtifactContent()}</div>
              </section>
            </div>
          </div>
        </div>
        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur xl:hidden">
          <h2 className="text-lg font-semibold text-white">成果物プレビュー</h2>
          <div className="mt-4">{renderArtifactContent()}</div>
        </section>

        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/40 p-6 backdrop-blur">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">会話エージェント</h2>
              <p className="text-sm text-slate-400">
                チャット経由でエージェントに制作指示を出したり、進捗を確認できます。
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleCreateChatSession()}
              disabled={isCreatingSession}
              className="rounded-lg border border-blue-500/60 px-4 py-2 text-sm font-semibold text-blue-100 transition hover:border-blue-400 hover:bg-blue-500/10 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
            >
              {isCreatingSession ? "セッション作成中..." : "新しいセッション"}
            </button>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[280px_1fr]">
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                セッション一覧
              </h3>
              <div className="space-y-2">
                {chatSessions.length ? (
                  chatSessions.map((session) => {
                    const isActive = session.id === selectedChatSessionId;
                    return (
                      <button
                        key={session.id}
                        type="button"
                        onClick={() => setSelectedChatSessionId(session.id)}
                        className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition ${
                          isActive
                            ? "border-blue-500/70 bg-blue-500/10 shadow"
                            : "border-slate-800 bg-slate-950/40 hover:border-blue-500/40 hover:bg-blue-500/5"
                        }`}
                      >
                        <span className="block font-semibold text-white">{session.title ?? `セッション #${session.id}`}</span>
                        <span className="mt-1 block text-xs text-slate-400">
                          ステータス: {session.status}
                        </span>
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
                  {selectedChatSession ? (
                    chatMessages.length ? (
                      chatMessages.map((message) => (
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

                <form className="mt-4 space-y-3" onSubmit={(event) => void handleSendChatMessage(event)}>
                  <textarea
                    value={chatInput}
                    onChange={(event) => setChatInput(event.target.value)}
                    disabled={!selectedChatSession || isSendingMessage}
                    className="h-24 w-full rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:cursor-not-allowed disabled:text-slate-500"
                    placeholder="生成したい成果物や進捗の確認事項を日本語で入力してください"
                  />
                  <div className="flex items-center justify-end">
                    <button
                      type="submit"
                      disabled={!selectedChatSession || isSendingMessage || !chatInput.trim()}
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
                  {selectedChatSession ? (
                    chatEvents.length ? (
                      chatEvents.map((event) => {
                        const payload = event.payload ?? {};
                        let description = JSON.stringify(payload);
                        if (event.type === "status") {
                          const phase = typeof payload.phase === "string" ? payload.phase : String(payload.phase ?? "unknown");
                          const intent = typeof payload.intent === "string" ? payload.intent : "";
                          description = `ステータス: ${phase} / intent: ${intent}`;
                        }
                        if (event.type === "artifact_update") {
                          const templateCode = typeof payload.template_code === "string" ? payload.template_code : "";
                          const label = templateLabelMap[templateCode] ?? templateCode;
                          const artifactId = typeof payload.artifact_id === "number" ? payload.artifact_id : payload.artifact_id ?? "-";
                          description = `${label || "成果物"} (ID: ${artifactId}) を更新しました`;
                        }
                        return (
                          <div
                            key={event.id}
                            className="rounded-xl border border-slate-800/80 bg-slate-950/70 px-3 py-2"
                          >
                            <p className="text-xs text-slate-400">{new Date(event.created_at).toLocaleTimeString()}</p>
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
      </div>
    </main>
  );
}
