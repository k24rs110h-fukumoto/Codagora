import {
  Bell,
  ChevronDown,
  Copy,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  Plus,
  Search,
  Settings,
  UserRoundPlus,
  Users,
} from "lucide-react";
import {
  NavLink,
  Outlet,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import Logo from "../components/Logo";
import LoadingScreen from "../components/LoadingScreen";
import Modal from "../components/Modal";
import { getErrorMessage } from "../lib/errors";
import {
  createChannel,
  createInviteCode,
  listChannels,
  listMembers,
  listWorkspaces,
} from "../services/codagoraApi";
import type {
  Channel,
  Workspace,
  WorkspaceMember,
  WorkspaceOutletContext,
} from "../types";

function WorkspaceLayout() {
  const navigate = useNavigate();
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [modal, setModal] = useState<"channel" | "invite" | "members" | null>(null);
  const [inviteCode, setInviteCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notice, setNotice] = useState<{
    message: string;
    tone: "success" | "error";
  } | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const showNotice = useCallback(
    (message: string, tone: "success" | "error" = "success") => {
      setNotice({ message, tone });
      window.setTimeout(() => setNotice(null), 3500);
    },
    [],
  );

  const reloadChannels = useCallback(async () => {
    if (!workspaceSlug) {
      return;
    }

    setChannels(await listChannels(workspaceSlug));
  }, [workspaceSlug]);

  useEffect(() => {
    if (!workspaceSlug) {
      return;
    }

    const currentSlug = workspaceSlug;
    const controller = new AbortController();

    async function loadWorkspace() {
      try {
        setIsLoading(true);
        setPageError("");

        const [workspaceList, channelList, memberResult] = await Promise.all([
          listWorkspaces(controller.signal),
          listChannels(currentSlug, controller.signal),
          listMembers(currentSlug, controller.signal).catch(() => []),
        ]);

        const selectedWorkspace = workspaceList.find(
          (item) => item.slug === currentSlug,
        );

        if (!selectedWorkspace) {
          throw new Error("ワークスペースが見つかりません。");
        }

        setWorkspace(selectedWorkspace);
        setChannels(channelList);
        setMembers(memberResult);
      } catch (error) {
        if (!controller.signal.aborted) {
          setPageError(
            getErrorMessage(error, "ワークスペースを読み込めませんでした。"),
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadWorkspace();

    return () => controller.abort();
  }, [workspaceSlug]);

  const workspaceInitial = useMemo(
    () => workspace?.name.trim().charAt(0).toUpperCase() || "C",
    [workspace],
  );

  async function handleCreateChannel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!workspaceSlug) {
      return;
    }

    const form = new FormData(event.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    const topic = String(form.get("topic") ?? "").trim();

    if (!name) {
      return;
    }

    try {
      setIsSubmitting(true);
      const channel = await createChannel(workspaceSlug, { name, topic });
      await reloadChannels();
      setModal(null);
      navigate(`/workspaces/${workspaceSlug}/channels/${channel.id}`);
      showNotice("チャンネルを作成しました。");
    } catch (error) {
      showNotice(
        getErrorMessage(error, "チャンネルを作成できませんでした。"),
        "error",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function openInviteModal() {
    if (!workspaceSlug) {
      return;
    }

    try {
      setModal("invite");
      setInviteCode("");
      setIsSubmitting(true);
      setInviteCode(await createInviteCode(workspaceSlug));
    } catch (error) {
      setModal(null);
      showNotice(
        getErrorMessage(error, "招待コードを発行できませんでした。"),
        "error",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function copyInviteCode() {
    await navigator.clipboard.writeText(inviteCode);
    showNotice("招待コードをコピーしました。");
  }

  if (isLoading) {
    return <LoadingScreen label="ワークスペースを読み込んでいます" />;
  }

  if (!workspaceSlug || !workspace || pageError) {
    return (
      <main className="center-state">
        <Logo />
        <h1>ワークスペースを開けません</h1>
        <p>{pageError || "URLを確認してください。"}</p>
        <button type="button" className="primary-button" onClick={() => navigate("/")}>
          一覧へ戻る
        </button>
      </main>
    );
  }

  const outletContext: WorkspaceOutletContext = {
    workspace,
    channels,
    members,
    reloadChannels,
    showNotice,
  };

  return (
    <div className="workspace-shell">
      <header className="app-header">
        <Logo to="/" />

        <button type="button" className="workspace-switcher" onClick={() => navigate("/")}>
          <span className="workspace-switcher-mark">{workspaceInitial}</span>
          <span>
            <small>Workspace</small>
            <strong>{workspace.name}</strong>
          </span>
          <ChevronDown size={15} />
        </button>

        <label className="app-search">
          <Search size={17} />
          <input placeholder="メッセージやメンバーを検索" />
          <kbd>⌘K</kbd>
        </label>

        <div className="app-header-actions">
          <button type="button" className="icon-button" aria-label="通知">
            <Bell size={18} />
          </button>

          <button
            type="button"
            className="secondary-button header-invite-button"
            onClick={() => void openInviteModal()}
          >
            <UserRoundPlus size={16} />
            招待
          </button>

          <button
            type="button"
            className="mobile-menu"
            onClick={() => setIsSidebarOpen((current) => !current)}
          >
            <Menu size={20} />
          </button>
        </div>
      </header>

      <div className="workspace-body">
        <aside className={`workspace-sidebar${isSidebarOpen ? " workspace-sidebar--open" : ""}`}>
          <nav className="workspace-nav">
            <span className="sidebar-label">Workspace</span>

            <NavLink
              end
              to={`/workspaces/${workspaceSlug}`}
              className={({ isActive }) =>
                `sidebar-link${isActive ? " sidebar-link--active" : ""}`
              }
              onClick={() => setIsSidebarOpen(false)}
            >
              <LayoutDashboard size={18} />
              <span>Overview</span>
            </NavLink>

            <button type="button" className="sidebar-link" onClick={() => setModal("members")}>
              <Users size={18} />
              <span>Members</span>
              <small>{members.length}</small>
            </button>
          </nav>

          <section className="channel-navigation">
            <header>
              <span className="sidebar-label">Channels</span>
              <button type="button" onClick={() => setModal("channel")}>
                <Plus size={16} />
              </button>
            </header>

            <nav>
              {channels.map((channel, index) => (
                <NavLink
                  key={channel.id}
                  to={`/workspaces/${workspaceSlug}/channels/${channel.id}`}
                  className={({ isActive }) =>
                    `channel-link${isActive ? " channel-link--active" : ""}`
                  }
                  onClick={() => setIsSidebarOpen(false)}
                >
                  <span className={`channel-dot channel-dot--${(index % 4) + 1}`} />
                  <span>
                    <strong>{channel.name}</strong>
                    <small>{channel.topic || "チームの会話"}</small>
                  </span>
                </NavLink>
              ))}
            </nav>

            {channels.length === 0 && (
              <button type="button" className="create-first-channel" onClick={() => setModal("channel")}>
                <MessageSquareText size={18} />
                最初のチャンネルを作成
              </button>
            )}
          </section>

          <footer className="sidebar-account">
            <span className="account-avatar">U</span>
            <span>
              <strong>ログイン中</strong>
              <small>Django session</small>
            </span>
            <button type="button" className="icon-button" aria-label="設定">
              <Settings size={17} />
            </button>
          </footer>
        </aside>

        <main className="workspace-main">
          <Outlet context={outletContext} />
        </main>
      </div>

      {notice && (
        <div className={`toast toast--${notice.tone}`}>{notice.message}</div>
      )}

      {modal === "channel" && (
        <Modal
          title="チャンネルを作成"
          description="話題ごとに会話を整理する場所を追加します。"
          onClose={() => setModal(null)}
        >
          <form className="stack-form" onSubmit={handleCreateChannel}>
            <label>
              チャンネル名
              <input name="name" placeholder="frontend" required />
            </label>

            <label>
              トピック
              <textarea name="topic" placeholder="このチャンネルで話す内容" rows={3} />
            </label>

            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "作成中..." : "作成する"}
            </button>
          </form>
        </Modal>
      )}

      {modal === "invite" && (
        <Modal
          title="メンバーを招待"
          description="このコードを参加してほしい人に共有してください。"
          onClose={() => setModal(null)}
        >
          <div className="invite-code-box">
            <span>{isSubmitting ? "発行中..." : inviteCode}</span>
            <button
              type="button"
              className="primary-button"
              onClick={() => void copyInviteCode()}
              disabled={!inviteCode}
            >
              <Copy size={16} />
              コピー
            </button>
          </div>
        </Modal>
      )}

      {modal === "members" && (
        <Modal
          title="ワークスペースメンバー"
          description={`${members.length}人が参加しています。`}
          onClose={() => setModal(null)}
        >
          <div className="modal-member-list">
            {members.map((member) => (
              <article key={member.id}>
                <span>{member.user.displayName.charAt(0).toUpperCase()}</span>
                <div>
                  <strong>{member.user.displayName}</strong>
                  <small>{member.user.email || member.user.username}</small>
                </div>
                <em>{member.role}</em>
              </article>
            ))}

            {members.length === 0 && (
              <p className="muted-copy">
                メンバーAPIのレスポンスが空、またはURLが一致していません。
              </p>
            )}
          </div>
        </Modal>
      )}

      <button
        type="button"
        className="floating-logout"
        title="ログアウト"
        onClick={() => window.location.assign("/api-auth/logout/?next=/")}
      >
        <LogOut size={17} />
      </button>
    </div>
  );
}

export default WorkspaceLayout;
