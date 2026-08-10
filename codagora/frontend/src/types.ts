export type Identifier = string | number;

export type Workspace = {
  id: Identifier;
  name: string;
  slug: string;
  description: string;
  role: string;
  inviteCode?: string;
};

export type WorkspaceMember = {
  id: Identifier;
  role: string;
  joinedAt?: string;
  user: {
    id: Identifier;
    username: string;
    displayName: string;
    email: string;
  };
};

export type Channel = {
  id: Identifier;
  name: string;
  topic: string;
  createdAt?: string;
};

export type MessageAuthor = {
  id: Identifier | null;
  username: string;
  displayName: string;
  email: string;
};

export type Message = {
  id: Identifier;
  author: MessageAuthor | null;
  authorName: string;
  content: string;
  parentId: Identifier | null;
  parentPreview: string;
  isDeleted: boolean;
  canEdit: boolean;
  createdAt: string;
  updatedAt?: string;
};

export type WorkspaceOutletContext = {
  workspace: Workspace;
  channels: Channel[];
  members: WorkspaceMember[];
  reloadChannels: () => Promise<void>;
  showNotice: (message: string, tone?: "success" | "error") => void;
};
