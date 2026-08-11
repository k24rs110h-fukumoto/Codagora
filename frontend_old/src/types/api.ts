export type ApiListResponse<T> =
  | T[]
  | {
      count?: number;
      next?: string | null;
      previous?: string | null;
      results: T[];
    };

export type UserSummary = {
  id: string | number;
  username?: string;
  display_name?: string;
  email?: string;
};

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  role?: string;
  created_at?: string;
  updated_at?: string;
};

export type Channel = {
  id: string;
  name: string;
  topic?: string | null;
  workspace?: string;
  created_at?: string;
  updated_at?: string;
};

export type MessageAuthor = UserSummary | string | null;

export type Message = {
  id: string;
  author: MessageAuthor;
  author_name?: string | null;
  content: string;
  parent?: string | Message | null;
  is_deleted?: boolean;
  created_at: string;
  updated_at?: string;
};

export function unwrapListResponse<T>(
  response: ApiListResponse<T>,
): T[] {
  if (Array.isArray(response)) {
    return response;
  }

  return response.results;
}