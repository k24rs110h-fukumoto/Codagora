import { type AxiosRequestConfig } from "axios";
import api from "../lib/api";
import {
  normalizeChannel,
  normalizeMember,
  normalizeMessage,
  normalizeWorkspace,
  unwrapList,
} from "../lib/normalizers";
import type {
  Channel,
  Identifier,
  Message,
  Workspace,
  WorkspaceMember,
} from "../types";

type Candidate = {
  url: string;
  config?: AxiosRequestConfig;
};

function getResponseStatus(error: unknown): number | undefined {
  if (!error || typeof error !== "object") {
    return undefined;
  }

  const response = (error as { response?: { status?: unknown } }).response;
  return typeof response?.status === "number" ? response.status : undefined;
}

async function tryCandidates<T>(
  method: "get" | "post" | "patch" | "delete",
  candidates: Candidate[],
  data?: unknown,
): Promise<T> {
  let lastError: unknown;

  for (const candidate of candidates) {
    try {
      const response =
        method === "get" || method === "delete"
          ? await api.request<T>({
              method,
              url: candidate.url,
              ...candidate.config,
            })
          : await api.request<T>({
              method,
              url: candidate.url,
              data,
              ...candidate.config,
            });

      return response.data;
    } catch (error) {
      lastError = error;

      if (![404, 405].includes(getResponseStatus(error) ?? 0)) {
        throw error;
      }
    }
  }

  throw lastError;
}

export async function listWorkspaces(
  signal?: AbortSignal,
): Promise<Workspace[]> {
  const response = await api.get("/api/workspaces/", { signal });
  return unwrapList(response.data).map(normalizeWorkspace);
}

export async function createWorkspace(data: {
  name: string;
  description: string;
}): Promise<Workspace> {
  const response = await api.post("/api/workspaces/", data);
  return normalizeWorkspace(response.data);
}

export async function joinWorkspace(inviteCode: string): Promise<Workspace | null> {
  const paths = [
    "/api/workspaces/join/",
    "/api/workspaces/join-by-code/",
    "/api/workspaces/invitations/join/",
  ];

  let lastError: unknown;

  for (const url of paths) {
    for (const payload of [
      { invite_code: inviteCode },
      { code: inviteCode },
      { invitation_code: inviteCode },
    ]) {
      try {
        const response = await api.post(url, payload);
        const record = response.data;

        if (record && typeof record === "object") {
          const workspaceValue =
            (record as Record<string, unknown>).workspace ?? record;
          const workspace = normalizeWorkspace(workspaceValue);

          return workspace.slug ? workspace : null;
        }

        return null;
      } catch (error) {
        lastError = error;

        if (![400, 404, 405].includes(getResponseStatus(error) ?? 0)) {
          throw error;
        }
      }
    }
  }

  throw lastError;
}

export async function listMembers(
  workspaceSlug: string,
  signal?: AbortSignal,
): Promise<WorkspaceMember[]> {
  const response = await api.get(
    `/api/workspaces/${encodeURIComponent(workspaceSlug)}/members/`,
    { signal },
  );

  return unwrapList(response.data).map(normalizeMember);
}

export async function createInviteCode(
  workspaceSlug: string,
): Promise<string> {
  const data = await tryCandidates<unknown>("post", [
    {
      url: `/api/workspaces/${encodeURIComponent(workspaceSlug)}/invite/`,
    },
    {
      url: `/api/workspaces/${encodeURIComponent(workspaceSlug)}/invite-code/`,
    },
    {
      url: `/api/workspaces/${encodeURIComponent(workspaceSlug)}/invitations/`,
    },
  ]);

  const record =
    data && typeof data === "object"
      ? (data as Record<string, unknown>)
      : {};

  const code = record.invite_code ?? record.code ?? record.invitation_code;

  if (typeof code !== "string") {
    throw new Error("招待コードをレスポンスから取得できませんでした。");
  }

  return code;
}

export async function listChannels(
  workspaceSlug: string,
  signal?: AbortSignal,
): Promise<Channel[]> {
  const response = await api.get(
    `/api/workspaces/${encodeURIComponent(workspaceSlug)}/channels/`,
    { signal },
  );

  return unwrapList(response.data).map(normalizeChannel);
}

export async function createChannel(
  workspaceSlug: string,
  data: { name: string; topic: string },
): Promise<Channel> {
  const response = await api.post(
    `/api/workspaces/${encodeURIComponent(workspaceSlug)}/channels/`,
    data,
  );

  return normalizeChannel(response.data);
}

export async function listMessages(
  workspaceSlug: string,
  channelId: Identifier,
  signal?: AbortSignal,
): Promise<Message[]> {
  const response = await api.get(
    `/api/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(String(channelId))}/messages/`,
    { signal },
  );

  return unwrapList(response.data).map(normalizeMessage);
}

export async function createMessage(
  workspaceSlug: string,
  channelId: Identifier,
  data: { content: string; parent?: Identifier | null },
): Promise<Message> {
  const response = await api.post(
    `/api/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(String(channelId))}/messages/`,
    data,
  );

  return normalizeMessage(response.data);
}

export async function updateMessage(
  workspaceSlug: string,
  channelId: Identifier,
  messageId: Identifier,
  content: string,
): Promise<Message> {
  const response = await api.patch(
    `/api/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(
      String(channelId),
    )}/messages/${encodeURIComponent(String(messageId))}/`,
    { content },
  );

  return normalizeMessage(response.data);
}

export async function deleteMessage(
  workspaceSlug: string,
  channelId: Identifier,
  messageId: Identifier,
): Promise<void> {
  await api.delete(
    `/api/workspaces/${encodeURIComponent(
      workspaceSlug,
    )}/channels/${encodeURIComponent(
      String(channelId),
    )}/messages/${encodeURIComponent(String(messageId))}/`,
  );
}
