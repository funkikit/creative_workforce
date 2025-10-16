"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";

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
  { code: "overall_spec", label: "Overall Spec", kind: "text" },
  { code: "character_design", label: "Character Design", kind: "text", requiresEpisode: true },
  { code: "background_sample", label: "Background Sample", kind: "text" },
  { code: "episode_summary", label: "Episode Summary", kind: "text", requiresEpisode: true },
  { code: "episode_script", label: "Episode Script", kind: "text", requiresEpisode: true },
  { code: "storyboard_table", label: "Storyboard Table", kind: "text", requiresEpisode: true },
  { code: "keyframe_image", label: "Keyframe Image", kind: "image", requiresEpisode: true },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [projectForm, setProjectForm] = useState({ name: "", description: "", episodes: 1 });
  const [instructions, setInstructions] = useState("Generate an overview of the story world.");
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

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );

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
      if (!response.ok) throw new Error("Failed to load projects");
      const data: Project[] = await response.json();
      setProjects(data);
      if (data.length && selectedProjectId == null) {
        setSelectedProjectId(data[0].id);
      }
    } catch (error) {
      console.error(error);
      setMessage("Failed to load projects. Ensure backend is running on 8000.");
    }
  }

  async function loadArtifacts(projectId: number) {
    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}/artifacts`);
      if (!response.ok) throw new Error("Failed to load artifacts");
      const data: Artifact[] = await response.json();
      setArtifacts(data);
    } catch (error) {
      console.error(error);
      setMessage("Failed to load artifacts");
    }
  }

  async function loadProgress(projectId: number) {
    try {
      const response = await fetch(`${API_BASE}/projects/${projectId}/progress`);
      if (!response.ok) throw new Error("Failed to load progress");
      const data: Progress = await response.json();
      setProgress(data);
    } catch (error) {
      console.error(error);
      setMessage("Failed to load progress");
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
      if (!response.ok) throw new Error("Failed to create project");
      setProjectForm({ name: "", description: "", episodes: 1 });
      setMessage("Project created");
      await loadProjects();
    } catch (error) {
      console.error(error);
      setMessage("Failed to create project");
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
        setMessage("Keyframe task queued. Run the worker to process it.");
      } else if (response.ok) {
        setMessage("Artifact generated");
        await loadArtifacts(selectedProject.id);
      } else {
        const text = await response.text();
        throw new Error(text);
      }
    } catch (error) {
      console.error(error);
      setMessage("Failed to generate artifact");
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
      if (!response.ok) throw new Error("Failed to load artifact content");
      const data: ArtifactContent = await response.json();
      setSelectedArtifactContent(data);
    } catch (error) {
      console.error(error);
      setMessage("Failed to load artifact content");
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
      if (!response.ok) throw new Error("Worker failed");
      setPendingKeyframe(null);
      setMessage("Keyframe generated by worker");
      await loadArtifacts(selectedProject.id);
    } catch (error) {
      console.error(error);
      setMessage("Failed to process keyframe task");
    } finally {
      setLoading(false);
    }
  }

  function renderArtifactContent() {
    if (!selectedArtifactContent) {
      return <p className="text-sm text-gray-500">Select an artifact to preview its content.</p>;
    }

    if (selectedArtifactContent.is_binary && selectedArtifactContent.content) {
      const dataUrl = `data:image/png;base64,${selectedArtifactContent.content}`;
      return (
        <div>
          <p className="text-sm text-gray-500">Binary asset preview:</p>
          <img src={dataUrl} alt="Generated keyframe" className="mt-2 max-h-64 border" />
        </div>
      );
    }

    return (
      <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded border bg-gray-50 p-3 text-sm">
        {selectedArtifactContent.content}
      </pre>
    );
  }

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 p-6">
      <header>
        <h1 className="text-3xl font-semibold">Creative Workforce PoC Console</h1>
        <p className="mt-2 text-gray-600">
          Minimal UI for verifying project CRUD, artifact generation, and worker execution.
        </p>
      </header>

      <section className="rounded border p-4">
        <h2 className="text-xl font-semibold">Create Project</h2>
        <form className="mt-4 flex flex-wrap items-end gap-4" onSubmit={handleCreateProject}>
          <label className="flex flex-col text-sm font-medium">
            Name
            <input
              required
              className="mt-1 rounded border px-3 py-2"
              value={projectForm.name}
              onChange={(event) => setProjectForm((prev) => ({ ...prev, name: event.target.value }))}
            />
          </label>
          <label className="flex flex-col text-sm font-medium">
            Description
            <input
              className="mt-1 rounded border px-3 py-2"
              value={projectForm.description}
              onChange={(event) =>
                setProjectForm((prev) => ({ ...prev, description: event.target.value }))
              }
            />
          </label>
          <label className="flex flex-col text-sm font-medium">
            Episodes
            <input
              type="number"
              min={1}
              className="mt-1 w-24 rounded border px-3 py-2"
              value={projectForm.episodes}
              onChange={(event) =>
                setProjectForm((prev) => ({ ...prev, episodes: Number(event.target.value) }))
              }
            />
          </label>
          <button
            type="submit"
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500"
          >
            Create
          </button>
        </form>
      </section>

      <section className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="rounded border p-4 md:col-span-1">
          <h2 className="text-xl font-semibold">Projects</h2>
          <ul className="mt-3 space-y-2">
            {projects.map((project) => (
              <li key={project.id}>
                <button
                  type="button"
                  onClick={() => setSelectedProjectId(project.id)}
                  className={`w-full rounded border px-3 py-2 text-left ${
                    selectedProjectId === project.id ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"
                  }`}
                >
                  <span className="font-medium">{project.name}</span>
                  <span className="block text-xs text-gray-500">
                    Episodes planned: {project.episodes_planned}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded border p-4 md:col-span-2">
          <h2 className="text-xl font-semibold">Artifacts</h2>
          {selectedProject ? (
            <>
              <div className="mt-3 flex flex-wrap gap-2">
                {TEMPLATES.map((template) => (
                  <button
                    key={template.code}
                    type="button"
                    disabled={loading}
                    onClick={() => void handleGenerate(template)}
                    className="rounded border px-3 py-2 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Generate {template.label}
                  </button>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap gap-4">
                <label className="flex flex-col text-sm font-medium">
                  Episode (optional)
                  <input
                    type="number"
                    min={1}
                    className="mt-1 w-24 rounded border px-3 py-2"
                    value={episode}
                    onChange={(event) =>
                      setEpisode(event.target.value === "" ? "" : Number(event.target.value))
                    }
                  />
                </label>
                <label className="flex-1 text-sm font-medium">
                  Instructions
                  <textarea
                    className="mt-1 h-24 w-full rounded border px-3 py-2"
                    value={instructions}
                    onChange={(event) => setInstructions(event.target.value)}
                  />
                </label>
              </div>

              {pendingKeyframe && (
                <div className="mt-3 flex items-center gap-3 rounded border border-dashed border-yellow-500 bg-yellow-50 p-3 text-sm">
                  <span>Keyframe task pending.</span>
                  <button
                    type="button"
                    className="rounded bg-yellow-600 px-3 py-1 text-white hover:bg-yellow-500"
                    onClick={() => void handleProcessKeyframe()}
                  >
                    Run worker now
                  </button>
                </div>
              )}

              <div className="mt-4 max-h-60 overflow-auto border">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-3 py-2 text-left">Template</th>
                      <th className="px-3 py-2 text-left">Episode</th>
                      <th className="px-3 py-2 text-left">Version</th>
                      <th className="px-3 py-2 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {artifacts.map((artifact) => (
                      <tr key={artifact.id} className="border-b last:border-0">
                        <td className="px-3 py-2 font-mono text-xs">{artifact.template_code}</td>
                        <td className="px-3 py-2">{artifact.episode ?? "-"}</td>
                        <td className="px-3 py-2">v{artifact.version}</td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            className="rounded border px-2 py-1 text-xs hover:bg-gray-100"
                            onClick={() => void handleViewArtifact(artifact)}
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-500">Select a project to manage artifacts.</p>
          )}
        </div>
      </section>

      <section className="rounded border p-4">
        <h2 className="text-xl font-semibold">Artifact Preview</h2>
        <div className="mt-3">{renderArtifactContent()}</div>
      </section>

      <section className="rounded border p-4">
        <h2 className="text-xl font-semibold">Progress Overview</h2>
        {progress ? (
          <div className="mt-3 space-y-4 text-sm">
            <div>
              <h3 className="font-medium">Global Templates</h3>
              <div className="mt-1 flex flex-wrap gap-2">
                <span className="rounded bg-green-100 px-2 py-1 text-green-800">
                  Completed: {progress.global.completed.join(", ") || "-"}
                </span>
                <span className="rounded bg-red-100 px-2 py-1 text-red-800">
                  Pending: {progress.global.pending.join(", ") || "-"}
                </span>
              </div>
            </div>
            <div className="space-y-2">
              {progress.episodes.map((episodeState) => (
                <div key={episodeState.episode} className="rounded border p-3">
                  <h4 className="font-medium">Episode {episodeState.episode}</h4>
                  <p className="mt-1 text-green-700">
                    Completed: {episodeState.completed.join(", ") || "-"}
                  </p>
                  <p className="text-red-700">
                    Pending: {episodeState.pending.join(", ") || "-"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Select a project to see progress.</p>
        )}
      </section>

      {message && (
        <div className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700">
          {message}
        </div>
      )}
    </main>
  );
}
