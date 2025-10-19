"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import { ArtifactPreview } from "../components/dashboard/artifact-preview";
import { ArtifactTable } from "../components/dashboard/artifact-table";
import { ChatPanel } from "../components/dashboard/chat-panel";
import { DashboardHero } from "../components/dashboard/dashboard-hero";
import { GenerationPanel } from "../components/dashboard/generation-panel";
import { ProjectOverview } from "../components/dashboard/project-overview";
import { ProjectSidebar, type ProjectFormState } from "../components/dashboard/project-sidebar";
import { ProgressSummary } from "../components/dashboard/progress-summary";
import { AppShell } from "../components/layout/app-shell";
import { trpc } from "../lib/trpc/client";
import type { ChatEvent, ChatMessage, ChatSession } from "../lib/types/chat";
import type {
  Artifact,
  ArtifactContent,
  GenerationTemplate,
  Progress,
  Project,
} from "../lib/types/dashboard";


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

type PendingKeyframeTask = {
  projectId: number;
  episode: number | null;
  instructions: string;
  createdBy: string;
} | null;

const DEFAULT_PROJECT_FORM: ProjectFormState = {
  name: "",
  description: "",
  episodes: 1,
};

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [projectForm, setProjectForm] = useState<ProjectFormState>(DEFAULT_PROJECT_FORM);
  const [instructions, setInstructions] = useState(
    "作品世界の概要と雰囲気が伝わる説明を日本語で作成してください。"
  );
  const [episode, setEpisode] = useState<number | "">(1);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedArtifactContent, setSelectedArtifactContent] = useState<ArtifactContent | null>(null);
  const [pendingKeyframe, setPendingKeyframe] = useState<PendingKeyframeTask>(null);
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
  const firstChatSessionId = chatSessions.length > 0 ? chatSessions[0].id : null;

  useEffect(() => {
    if (selectedChatSessionId == null && firstChatSessionId != null) {
      setSelectedChatSessionId(firstChatSessionId);
    }
  }, [firstChatSessionId, selectedChatSessionId]);

  const chatMessages = chatMessagesQuery.data?.items ?? [];
  const chatEvents = chatEventsQuery.data?.items ?? [];
  const isCreatingSession = chatCreateSession.isPending;
  const isSendingMessage = chatSendMessage.isPending;

  const loadProjects = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/projects`);
      if (!response.ok) throw new Error("プロジェクト一覧の取得に失敗しました");
      const data: Project[] = await response.json();
      setProjects(data);
      setSelectedProjectId((current) => {
        if (current != null) {
          return current;
        }
        return data.length > 0 ? data[0].id : current;
      });
    } catch (error) {
      console.error(error);
      setMessage("プロジェクト一覧の取得に失敗しました。バックエンドがポート8000で起動しているか確認してください。");
    }
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (selectedProjectId != null) {
      void Promise.all([loadArtifacts(selectedProjectId), loadProgress(selectedProjectId)]);
    }
  }, [selectedProjectId]);

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

  function handleProjectFieldChange(field: keyof ProjectFormState, value: string | number) {
    setProjectForm((prev) => {
      if (field === "episodes") {
        const numericValue = typeof value === "number" ? value : Number(value);
        return {
          ...prev,
          episodes: Number.isNaN(numericValue) ? 1 : Math.max(1, numericValue),
        };
      }

      if (field === "name") {
        return { ...prev, name: String(value) };
      }

      return { ...prev, description: String(value) };
    });
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
      setProjectForm({ ...DEFAULT_PROJECT_FORM });
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

  const sidebarPanel = (
    <ProjectSidebar
      projects={projects}
      selectedProjectId={selectedProjectId}
      onSelectProject={(projectId) => setSelectedProjectId(projectId)}
      projectForm={projectForm}
      onProjectFieldChange={handleProjectFieldChange}
      onCreateProject={handleCreateProject}
      className="space-y-6"
    />
  );

  const messageBanner = message ? (
    <div className="mt-6 rounded-2xl border border-brand-500/30 bg-brand-500/10 px-5 py-4 text-sm text-brand-100 backdrop-blur">
      {message}
    </div>
  ) : null;

  return (
    <AppShell
      sidebar={sidebarPanel}
      mobileSidebar={<ProjectSidebar
        projects={projects}
        selectedProjectId={selectedProjectId}
        onSelectProject={(projectId) => setSelectedProjectId(projectId)}
        projectForm={projectForm}
        onProjectFieldChange={handleProjectFieldChange}
        onCreateProject={handleCreateProject}
        className="mt-6 space-y-6"
      />}
      hero={
        <DashboardHero
          eyebrow="Creative Workforce"
          headline="コンソールで制作フローをオーガナイズ"
          description="プロジェクトの登録から成果物生成、ワーカー処理までをひとつの画面で把握し、PoC の検証をスムーズに進めましょう。"
          stats={stats}
        />
      }
      message={messageBanner}
    >
      <div className="space-y-8 pt-8">
        <ProjectOverview project={selectedProject} progress={progress} artifacts={artifacts} />
        <GenerationPanel
          templates={TEMPLATES}
          instructions={instructions}
          onInstructionsChange={setInstructions}
          episode={episode}
          onEpisodeChange={setEpisode}
          onGenerate={(template) => void handleGenerate(template)}
          disabled={generationDisabled}
          pendingKeyframe={pendingKeyframe}
          onProcessKeyframe={() => void handleProcessKeyframe()}
          requiresProjectSelection={!selectedProject}
        />
        <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <div className="space-y-6">
            <ArtifactTable
              artifacts={artifacts}
              templateLabelMap={templateLabelMap}
              onSelectArtifact={(artifact) => void handleViewArtifact(artifact)}
              projectSelected={Boolean(selectedProject)}
            />
            <ProgressSummary progress={progress} templateLabelMap={templateLabelMap} />
          </div>
          <ArtifactPreview artifactContent={selectedArtifactContent} className="hidden xl:block" />
        </div>
        <ArtifactPreview artifactContent={selectedArtifactContent} className="xl:hidden" />
        <ChatPanel
          sessions={chatSessions}
          selectedSessionId={selectedChatSessionId}
          onSelectSession={(sessionId) => setSelectedChatSessionId(sessionId)}
          onCreateSession={() => void handleCreateChatSession()}
          isCreatingSession={isCreatingSession}
          messages={chatMessages}
          events={chatEvents}
          chatInput={chatInput}
          onChatInputChange={setChatInput}
          onSendMessage={(event) => void handleSendChatMessage(event)}
          isSendingMessage={isSendingMessage}
          templateLabelMap={templateLabelMap}
        />
      </div>
    </AppShell>
  );
}
