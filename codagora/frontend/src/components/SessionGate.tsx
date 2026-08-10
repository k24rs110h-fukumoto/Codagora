import { LogIn, RefreshCw, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { getErrorMessage, isAuthenticationError } from "../lib/errors";
import { listWorkspaces } from "../services/codagoraApi";
import LoadingScreen from "./LoadingScreen";
import Logo from "./Logo";

type SessionGateProps = {
  children: ReactNode;
};

type SessionState = "loading" | "authenticated" | "unauthenticated" | "error";

function SessionGate({ children }: SessionGateProps) {
  const [state, setState] = useState<SessionState>("loading");
  const [errorMessage, setErrorMessage] = useState("");

  const checkSession = useCallback(async () => {
    try {
      setState("loading");
      setErrorMessage("");
      await listWorkspaces();
      setState("authenticated");
    } catch (error) {
      if (isAuthenticationError(error)) {
        setState("unauthenticated");
        return;
      }

      setErrorMessage(
        getErrorMessage(error, "Django APIへ接続できませんでした。"),
      );
      setState("error");
    }
  }, []);

  useEffect(() => {
    void checkSession();
  }, [checkSession]);

  if (state === "loading") {
    return <LoadingScreen label="ログイン状態を確認しています" />;
  }

  if (state === "unauthenticated") {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <Logo />

          <span className="auth-icon">
            <ShieldCheck size={28} />
          </span>

          <h1>開発チームの流れを、ひとつに。</h1>

          <p>
            Codagoraは、ワークスペース、チャンネル、メッセージをまとめて管理する
            開発者向けコラボレーションアプリです。
          </p>

          <button
            type="button"
            className="primary-button auth-login-button"
            onClick={() => {
              window.location.assign("/api-auth/login/?next=/");
            }}
          >
            <LogIn size={17} />
            Djangoでログイン
          </button>

          <small>
            バックエンドで使用しているDjangoアカウントでログインします。
          </small>
        </section>

        <aside className="auth-visual">
          <span className="auth-visual-label">CODAGORA WORKFLOW</span>

          <div className="auth-flow-card auth-flow-card--one">
            <strong>01</strong>
            <span>Workspace</span>
            <p>チームとプロジェクトを整理</p>
          </div>

          <div className="auth-flow-card auth-flow-card--two">
            <strong>02</strong>
            <span>Conversation</span>
            <p>相談と決定を共有</p>
          </div>

          <div className="auth-flow-card auth-flow-card--three">
            <strong>03</strong>
            <span>Build</span>
            <p>実装へつなげる</p>
          </div>
        </aside>
      </main>
    );
  }

  if (state === "error") {
    return (
      <main className="center-state">
        <Logo />
        <h1>バックエンドに接続できません</h1>
        <p>{errorMessage}</p>

        <button type="button" className="primary-button" onClick={checkSession}>
          <RefreshCw size={16} />
          再接続
        </button>

        <code>python manage.py runserver 127.0.0.1:8000</code>
      </main>
    );
  }

  return children;
}

export default SessionGate;
