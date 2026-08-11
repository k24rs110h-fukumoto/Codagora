import api from "../lib/api";
import {
  unwrapListResponse,
  type ApiListResponse,
  type Message,
} from "../types/api";

type CreateMessageData = {
  content: string;
  parent?: string | null;
};

export async function getMessages(
  workspaceSlug: string,
  channelId: string,
  signal?: AbortSignal,
): Promise<Message[]> {
  const response = await api.get<ApiListResponse<Message>>(
    `/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(channelId)}/messages/`,
    {
      signal,
    },
  );

  return unwrapListResponse(response.data);
}

export async function createMessage(
  workspaceSlug: string,
  channelId: string,
  data: CreateMessageData,
): Promise<Message> {
  const response = await api.post<Message>(
    `/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(channelId)}/messages/`,
    data,
  );

  return response.data;
}