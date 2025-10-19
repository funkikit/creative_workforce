export type Project = {
  id: number;
  name: string;
  description?: string | null;
  episodes_planned: number;
};

export type Artifact = {
  id: number;
  template_code: string;
  episode?: number | null;
  version: number;
  storage_path: string;
  status: string;
  created_by: string;
  created_at: string;
};

export type Progress = {
  global: { completed: string[]; pending: string[] };
  episodes: Array<{ episode: number; completed: string[]; pending: string[] }>;
};

export type ArtifactContent = {
  artifact: Artifact;
  content: string | null;
  content_type: string;
  is_binary: boolean;
};

export type GenerationTemplate = {
  code: string;
  label: string;
  kind: "text" | "image";
  requiresEpisode?: boolean;
};
