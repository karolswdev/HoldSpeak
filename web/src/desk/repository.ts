import { apiFetch } from "../lib/api";

export interface RepoFile {
  name: string;
  path: string;
  type: "file" | "dir";
  status?: "M" | "A" | "D" | "?" | null;
  modified?: string | null;
}

export interface RepoStatus {
  branch: string;
  dirty: number;
  ahead: number;
  behind: number;
}

export interface RepositoryRecord {
  kind: "repository";
  id: string;
  name: string;
  source_id: string;
  branch: string;
  created_at: string;
}

const repoUrl = (repositoryId: string, suffix = "") =>
  `/api/repositories/${encodeURIComponent(repositoryId)}${suffix}`;

export async function fetchRepositories(): Promise<RepositoryRecord[]> {
  const data = await apiFetch<{ repositories: RepositoryRecord[] }>("/api/repositories");
  return data.repositories ?? [];
}

export async function registerRepository(input: { sourceId?: string; path?: string; label?: string }) {
  return apiFetch<{ repository: RepositoryRecord }>("/api/repositories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: input.sourceId, path: input.path, label: input.label }),
  });
}

export async function fetchTree(repositoryId: string, path = ""): Promise<RepoFile[]> {
  const query = path ? `?path=${encodeURIComponent(path)}` : "";
  const data = await apiFetch<{ files: RepoFile[] }>(repoUrl(repositoryId, `/tree${query}`));
  return data.files ?? [];
}

export async function fetchFile(repositoryId: string, path: string): Promise<string> {
  const data = await apiFetch<{ content: string }>(repoUrl(repositoryId, `/file/${path.split("/").map(encodeURIComponent).join("/")}`));
  return data.content;
}

export async function writeFile(repositoryId: string, path: string, content: string) {
  return apiFetch(repoUrl(repositoryId, `/file/${path.split("/").map(encodeURIComponent).join("/")}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

export async function stageFiles(repositoryId: string, paths: string[]) {
  return apiFetch<{ staged: string[] }>(repoUrl(repositoryId, "/stage"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
}

export async function commit(repositoryId: string, message: string) {
  return apiFetch<{ committed: boolean; summary: string }>(repoUrl(repositoryId, "/commit"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

export function fetchStatus(repositoryId: string) {
  return apiFetch<RepoStatus>(repoUrl(repositoryId, "/status"));
}

export async function fetchBranches(repositoryId: string): Promise<string[]> {
  const data = await apiFetch<{ branches: string[] }>(repoUrl(repositoryId, "/branches"));
  return data.branches ?? [];
}

export function checkout(repositoryId: string, branch: string) {
  return apiFetch<RepoStatus>(repoUrl(repositoryId, "/checkout"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ branch }),
  });
}
