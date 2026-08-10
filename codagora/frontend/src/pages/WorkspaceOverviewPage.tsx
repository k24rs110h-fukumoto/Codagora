import {
  ArrowRight,
  Hash,
  MessageSquareText,
  Plus,
  UserRoundPlus,
  Users,
} from "lucide-react";
import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import type { WorkspaceOutletContext } from "../types";

function WorkspaceOverviewPage() {
  const navigate = useNavigate();
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const { workspace, channels, members } =
    useOutletContext<WorkspaceOutletContext>();

  const dateLabel = new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  }).format(new Date());

  return (
    <div className="overview-page">
      <section className="overview-hero">
        <div>
          <span className="eyebrow">{dateLabel}</span>
          <h1>{workspace.name}</h1>
          <p>
            {workspace.description ||
              "チームの会話と開発状況をここから確認できます。"}
          </p>
        </div>

        <div className="overview-hero-mark">
          {workspace.name.charAt(0).toUpperCase()}
        </div>
      </section>

      <section className="metric-grid">
        <article>
          <span className="metric-icon metric-icon--green">
            <Hash size={20} />
          </span>
          <div>
            <small>Channels</small>
            <strong>{channels.length}</strong>
          </div>
        </article>

        <article>
          <span className="metric-icon metric-icon--orange">
            <Users size={20} />
          </span>
          <div>
            <small>Members</small>
            <strong>{members.length}</strong>
          </div>
        </article>

        <article>
          <span className="metric-icon metric-icon--purple">
            <MessageSquareText size={20} />
          </span>
          <div>
            <small>Workspace role</small>
            <strong className="metric-role">{workspace.role}</strong>
          </div>
        </article>
      </section>

      <section className="overview-grid">
        <article className="panel-card">
          <header className="panel-header">
            <div>
              <span className="eyebrow">CONVERSATIONS</span>
              <h2>チャンネル</h2>
            </div>

            <span>{channels.length}</span>
          </header>

          <div className="overview-channel-list">
            {channels.map((channel, index) => (
              <button
                key={channel.id}
                type="button"
                onClick={() =>
                  navigate(
                    `/workspaces/${workspaceSlug}/channels/${channel.id}`,
                  )
                }
              >
                <span className={`overview-channel-number overview-channel-number--${(index % 4) + 1}`}>
                  {String(index + 1).padStart(2, "0")}
                </span>

                <span>
                  <strong>{channel.name}</strong>
                  <small>{channel.topic || "チームの会話"}</small>
                </span>

                <ArrowRight size={16} />
              </button>
            ))}

            {channels.length === 0 && (
              <div className="panel-empty">
                <Plus size={21} />
                <p>左メニューの＋からチャンネルを作成してください。</p>
              </div>
            )}
          </div>
        </article>

        <article className="panel-card">
          <header className="panel-header">
            <div>
              <span className="eyebrow">TEAM</span>
              <h2>参加メンバー</h2>
            </div>

            <UserRoundPlus size={19} />
          </header>

          <div className="overview-member-list">
            {members.slice(0, 6).map((member, index) => (
              <div key={member.id}>
                <span className={`overview-member-avatar overview-member-avatar--${(index % 4) + 1}`}>
                  {member.user.displayName.charAt(0).toUpperCase()}
                </span>
                <span>
                  <strong>{member.user.displayName}</strong>
                  <small>{member.role}</small>
                </span>
              </div>
            ))}

            {members.length === 0 && (
              <p className="muted-copy">
                メンバー情報はまだ取得できていません。
              </p>
            )}
          </div>
        </article>
      </section>
    </div>
  );
}

export default WorkspaceOverviewPage;
