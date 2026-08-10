import {
  ArrowRight,
  LogOut,
  Plus,
  RefreshCw,
  Sparkles,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import Modal from "../components/Modal";
import { getErrorMessage } from "../lib/errors";
import {
  createWorkspace,
  joinWorkspace,
  listWorkspaces,
} from "../services/codagoraApi";
import type { Workspace } from "../types";

function WorkspaceListPage() {
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [modal, setModal] = useState<"create" | "join" | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadWorkspaces = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMessage("");
      setWorkspaces(await listWorkspaces());
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "ワークスペースを取得できませんでした。"),
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkspaces();
  }, [loadWorkspaces]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    const description = String(form.get("description") ?? "").trim();

    if (!name) {
      return;
    }

    try {
      setIsSubmitting(true);
      const workspace = await createWorkspace({ name, description });
      setModal(null);
      navigate(`/workspaces/${workspace.slug}`);
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "ワークスペースを作成できませんでした。"),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleJoin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const inviteCode = String(form.get("inviteCode") ?? "").trim();

    if (!inviteCode) {
      return;
    }

    try {
      setIsSubmitting(true);
      const workspace = await joinWorkspace(inviteCode);
      setModal(null);

      if (workspace?.slug) {
        navigate(`/workspaces/${workspace.slug}`);
        return;
      }

      await loadWorkspaces();
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "招待コードで参加できませんでした。"),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="workspace-list-page">
      <header className="landing-header">
        <Logo />

        <button
          type="button"
          className="ghost-button"
          onClick={() => window.location.assign("/api-auth/logout/?next=/")}
        >
          <LogOut size={16} />
          ログアウト
        </button>
      </header>

      <section className="workspace-list-hero">
        <span className="eyebrow">
          <Sparkles size={14} />
          YOUR WORKSPACES
        </span>

        <h1>今日取り組む場所を選びましょう。</h1>

        <p>
          参加中のチームを開くか、新しいワークスペースを作成してください。
        </p>

        <div className="hero-actions">
          <button
            type="button"
            className="primary-button"
            onClick={() => setModal("create")}
          >
            <Plus size={17} />
            新規作成
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={() => setModal("join")}
          >
            <Users size={17} />
            招待コードで参加
          </button>
        </div>
      </section>

      {errorMessage && (
        <div className="alert alert--error">
          <span>{errorMessage}</span>
          <button type="button" onClick={() => void loadWorkspaces()}>
            <RefreshCw size={15} />
          </button>
        </div>
      )}

      <section className="workspace-grid">
        {isLoading &&
          Array.from({ length: 3 }).map((_, index) => (
            <article key={index} className="workspace-card workspace-card--skeleton" />
          ))}

        {!isLoading &&
          workspaces.map((workspace, index) => (
            <button
              key={workspace.id}
              type="button"
              className="workspace-card"
              onClick={() => navigate(`/workspaces/${workspace.slug}`)}
            >
              <span className={`workspace-card-mark workspace-card-mark--${(index % 4) + 1}`}>
                {workspace.name.charAt(0).toUpperCase()}
              </span>

              <span className="workspace-card-copy">
                <small>{workspace.role}</small>
                <strong>{workspace.name}</strong>
                <p>{workspace.description || "説明はまだ設定されていません。"}</p>
              </span>

              <span className="workspace-card-arrow">
                <ArrowRight size={18} />
              </span>
            </button>
          ))}
      </section>

      {!isLoading && workspaces.length === 0 && (
        <section className="empty-workspace">
          <span>C</span>
          <h2>ワークスペースがありません</h2>
          <p>新しく作成するか、招待コードを使って参加してください。</p>
        </section>
      )}

      {modal === "create" && (
        <Modal
          title="ワークスペースを作成"
          description="チームやプロジェクトの作業場所を作成します。"
          onClose={() => setModal(null)}
        >
          <form className="stack-form" onSubmit={handleCreate}>
            <label>
              ワークスペース名
              <input name="name" placeholder="Codagora Development" required />
            </label>

            <label>
              説明
              <textarea
                name="description"
                placeholder="このワークスペースの目的"
                rows={4}
              />
            </label>

            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "作成中..." : "作成する"}
            </button>
          </form>
        </Modal>
      )}

      {modal === "join" && (
        <Modal
          title="招待コードで参加"
          description="共有された招待コードを入力してください。"
          onClose={() => setModal(null)}
        >
          <form className="stack-form" onSubmit={handleJoin}>
            <label>
              招待コード
              <input
                name="inviteCode"
                placeholder="例: ABCD-1234"
                autoComplete="off"
                required
              />
            </label>

            <button type="submit" className="primary-button" disabled={isSubmitting}>
              {isSubmitting ? "参加中..." : "参加する"}
            </button>
          </form>
        </Modal>
      )}
    </main>
  );
}

export default WorkspaceListPage;
