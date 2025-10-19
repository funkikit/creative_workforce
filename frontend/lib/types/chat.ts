export type ChatSession = {
  id: number;
  project_id: number | null;
  title: string | null;
  status: "active" | "closed" | "archived";
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: number;
  session_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  extra: Record<string, unknown> | null;
  created_at: string;
};

export type ChatEvent = {
  id: number;
  session_id: number;
  type: "message" | "status" | "artifact_update" | "task_progress";
  payload: Record<string, unknown>;
  created_at: string;
};

