import api from "../lib/api";
import {
  unwrapListResponse,
  type ApiListResponse,
  type Workspace,
} from "../types/api";

export async function getWorkspaces(
  signal?: AbortSignal,
): Promise<Workspace[]> {
  const response = await api.get<ApiListResponse<Workspace>>(
    "/workspaces/",
    {
      signal,
    },
  );

  return unwrapListResponse(response.data);
}

export async function getWorkspace(
  workspaceSlug: string,
  signal?: AbortSignal,
): Promise<Workspace> {
  const response = await api.get<Workspace>(
    `/workspaces/${encodeURIComponent(workspaceSlug)}/`,
    {
      signal,
    },
  );

  return response.data;
}