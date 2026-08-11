import type {
  Channel,
  Identifier,
  Message,
  MessageAuthor,
  Workspace,
  WorkspaceMember,
} from "../types";

type UnknownRecord = Record<string, unknown>;

function asRecord(value: unknown): UnknownRecord {
  return value && typeof value === "object" ? (value as UnknownRecord) : {};
}

function text(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function id(value: unknown, fallback: Identifier = ""): Identifier {
  return typeof value === "string" || typeof value === "number"
    ? value
    : fallback;
}

function bool(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

export function unwrapList(value: unknown): unknown[] {
  if (Array.isArray(value)) {
    return value;
  }

  const record = asRecord(value);

  if (Array.isArray(record.results)) {
    return record.results;
  }

  return [];
}

export function normalizeWorkspace(value: unknown): Workspace {
  const record = asRecord(value);

  return {
    id: id(record.id),
    name: text(record.name, "Untitled workspace"),
    slug: text(record.slug),
    description: text(record.description),
    role: text(record.role ?? record.current_user_role, "member"),
    inviteCode: text(record.invite_code ?? record.code) || undefined,
  };
}

export function normalizeChannel(value: unknown): Channel {
  const record = asRecord(value);

  return {
    id: id(record.id),
    name: text(record.name, "Untitled"),
    topic: text(record.topic ?? record.description),
    createdAt: text(record.created_at),
  };
}

export function normalizeMember(value: unknown): WorkspaceMember {
  const record = asRecord(value);
  const user = asRecord(record.user ?? record.account);

  return {
    id: id(record.id ?? user.id),
    role: text(record.role, "member"),
    joinedAt: text(record.joined_at) || undefined,
    user: {
      id: id(user.id ?? record.user_id),
      username: text(user.username ?? record.username, "member"),
      displayName: text(
        user.display_name ??
          user.displayName ??
          user.full_name ??
          record.display_name ??
          user.username,
        "Member",
      ),
      email: text(user.email ?? record.email),
    },
  };
}

function normalizeAuthor(value: unknown): MessageAuthor | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "string") {
    return {
      id: null,
      username: value,
      displayName: value,
      email: "",
    };
  }

  const record = asRecord(value);

  return {
    id: record.id === null || record.id === undefined ? null : id(record.id),
    username: text(record.username, "member"),
    displayName: text(
      record.display_name ?? record.displayName ?? record.username,
      "Member",
    ),
    email: text(record.email),
  };
}

export function normalizeMessage(value: unknown): Message {
  const record = asRecord(value);
  const parent = asRecord(record.parent);
  const author = normalizeAuthor(record.author);
  const authorName = text(
    record.author_name,
    author?.displayName || author?.username || "削除済みユーザー",
  );

  return {
    id: id(record.id),
    author,
    authorName,
    content: text(record.content),
    parentId:
      record.parent === null || record.parent === undefined
        ? null
        : id(parent.id ?? record.parent),
    parentPreview: text(
      parent.content ?? record.parent_content ?? record.reply_to_content,
    ),
    isDeleted: bool(record.is_deleted),
    canEdit: bool(record.can_edit ?? record.is_mine, true),
    createdAt: text(record.created_at),
    updatedAt: text(record.updated_at) || undefined,
  };
}
