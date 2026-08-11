import api from "../lib/api";
import {
  unwrapListResponse,
  type ApiListResponse,
  type Channel,
} from "../types/api";

export async function getChannels(
  workspaceSlug: string,
  signal?: AbortSignal,
): Promise<Channel[]> {
  const response = await api.get<ApiListResponse<Channel>>(
    `/workspaces/${encodeURIComponent(workspaceSlug)}/channels/`,
    {
      signal,
    },
  );

  return unwrapListResponse(response.data);
}

export async function getChannel(
  workspaceSlug: string,
  channelId: string,
  signal?: AbortSignal,
): Promise<Channel> {
  const response = await api.get<Channel>(
    `/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(channelId)}/`,
    {
      signal,
    },
  );

  return response.data;
}