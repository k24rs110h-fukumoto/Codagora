import { useEffect, useState } from "react";
import { Link } from "react-router";
import { getApiErrorMessage } from "../lib/getApiErrorMessage";
import { getWorkspaces } from "../services/workspaceService";
import type { Workspace } from "../types/api";

function WorkspaceSelectPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadWorkspaces() {
      try {
        setIsLoading(true);
        setErrorMessage("");

        const workspaceList = await getWorkspaces(
          controller.signal,
        );

        setWorkspaces(workspaceList);
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        setErrorMessage(
          getApiErrorMessage(
            error,
            "ワークスペースの取得に失敗しました。",
          ),
        );
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadWorkspaces();

    return () => {
      controller.abort();
    };
  }, []);

  return (
    <main className="workspace-select-page">
      <section className="workspace-select-card">
        <div className="workspace-select-logo">C</div>

        <h1>Codagora</h1>

        <p>
          参加するワークスペースを選択してください。
        </p>

        {isLoading && (
          <div className="page-status">
            ワークスペースを読み込んでいます...
          </div>
        )}

        {errorMessage && (
          <div className="page-error">
            <strong>読み込みエラー</strong>
            <span>{errorMessage}</span>
          </div>
        )}

        {!isLoading &&
          !errorMessage &&
          workspaces.length === 0 && (
            <div className="workspace-empty-notice">
              参加中のワークスペースがありません。
            </div>
          )}

        <div className="workspace-select-list">
          {workspaces.map((workspace) => (
            <Link
              key={workspace.id}
              to={`/app/workspaces/${workspace.slug}`}
              className="workspace-select-item"
            >
              <div className="workspace-select-avatar">
                {workspace.name.charAt(0).toUpperCase()}
              </div>

              <div>
                <strong>{workspace.name}</strong>

                <span>
                  {workspace.description ||
                    "ワークスペースを開く"}
                </span>
              </div>

              <span className="workspace-select-arrow">
                →
              </span>
            </Link>
          ))}
        </div>

        <button
          type="button"
          className="workspace-create-button"
        >
          新しいワークスペースを作成
        </button>
      </section>
    </main>
  );
}

export default WorkspaceSelectPage;