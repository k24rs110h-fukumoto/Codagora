import {
  CornerUpLeft,
  Edit3,
  MoreHorizontal,
  Send,
  Trash2,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { useOutletContext, useParams } from "react-router-dom";
import { getErrorMessage } from "../lib/errors";
import {
  createMessage,
  deleteMessage,
  listMessages,
  updateMessage,
} from "../services/codagoraApi";
import type {
  Identifier,
  Message,
  WorkspaceOutletContext,
} from "../types";

function formatDate(value: string): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function ChannelPage() {
  const { workspaceSlug, channelId } = useParams<{
    workspaceSlug: string;
    channelId: string;
  }>();
  const { channels, showNotice } =
    useOutletContext<WorkspaceOutletContext>();

  const channel = useMemo(
    () => channels.find((item) => String(item.id) === channelId),
    [channels, channelId],
  );

  const [messages, setMessages] = useState<Message[]>([]);
  const [messageText, setMessageText] = useState("");
  const [replyTarget, setReplyTarget] = useState<Message | null>(null);
  const [editingId, setEditingId] = useState<Identifier | null>(null);
  const [editingText, setEditingText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadMessages = useCallback(async () => {
    if (!workspaceSlug || !channelId) {
      return;
    }

    try {
      setIsLoading(true);
      setErrorMessage("");
      setMessages(await listMessages(workspaceSlug, channelId));
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error, "メッセージを取得できませんでした。"),
      );
    } finally {
      setIsLoading(false);
    }
  }, [workspaceSlug, channelId]);

  useEffect(() => {
    void loadMessages();
  }, [loadMessages]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!workspaceSlug || !channelId || isSending) {
      return;
    }

    const content = messageText.trim();

    if (!content) {
      return;
    }

    try {
      setIsSending(true);
      const created = await createMessage(workspaceSlug, channelId, {
        content,
        parent: replyTarget?.id ?? null,
      });

      setMessages((current) => [...current, created]);
      setMessageText("");
      setReplyTarget(null);
    } catch (error) {
      showNotice(
        getErrorMessage(error, "メッセージを送信できませんでした。"),
        "error",
      );
    } finally {
      setIsSending(false);
    }
  }

  async function handleEdit(messageId: Identifier) {
    if (!workspaceSlug || !channelId) {
      return;
    }

    const content = editingText.trim();

    if (!content) {
      return;
    }

    try {
      const updated = await updateMessage(
        workspaceSlug,
        channelId,
        messageId,
        content,
      );

      setMessages((current) =>
        current.map((message) =>
          String(message.id) === String(messageId) ? updated : message,
        ),
      );
      setEditingId(null);
      setEditingText("");
      showNotice("メッセージを編集しました。");
    } catch (error) {
      showNotice(
        getErrorMessage(error, "メッセージを編集できませんでした。"),
        "error",
      );
    }
  }

  async function handleDelete(messageId: Identifier) {
    if (
      !workspaceSlug ||
      !channelId ||
      !window.confirm("このメッセージを削除しますか？")
    ) {
      return;
    }

    try {
      await deleteMessage(workspaceSlug, channelId, messageId);

      setMessages((current) =>
        current.map((message) =>
          String(message.id) === String(messageId)
            ? { ...message, content: "", isDeleted: true }
            : message,
        ),
      );
      showNotice("メッセージを削除しました。");
    } catch (error) {
      showNotice(
        getErrorMessage(error, "メッセージを削除できませんでした。"),
        "error",
      );
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  if (!workspaceSlug || !channelId) {
    return null;
  }

  return (
    <div className="channel-page">
      <header className="channel-page-header">
        <div>
          <span className="eyebrow">CHANNEL</span>
          <h1>{channel?.name ?? "Channel"}</h1>
          <p>{channel?.topic || "チームの会話と更新を共有する場所です。"}</p>
        </div>

        <span className="channel-message-count">
          <strong>{messages.length}</strong>
          messages
        </span>
      </header>

      {errorMessage && (
        <div className="alert alert--error">
          <span>{errorMessage}</span>
          <button type="button" onClick={() => void loadMessages()}>
            再読み込み
          </button>
        </div>
      )}

      <section className="conversation">
        <div className="conversation-divider">
          <span>Conversation</span>
        </div>

        {isLoading && (
          <div className="message-loading">
            <span className="loading-spinner" />
            メッセージを読み込んでいます
          </div>
        )}

        {!isLoading && messages.length === 0 && (
          <div className="conversation-empty">
            <MessageEmptyIcon />
            <h2>最初のメッセージを送りましょう</h2>
            <p>質問、進捗、アイデアをこのチャンネルに共有できます。</p>
          </div>
        )}

        <div className="message-timeline">
          {messages.map((message, index) => (
            <article
              key={message.id}
              className={`message-card${message.parentId ? " message-card--reply" : ""}`}
            >
              <span className={`message-avatar message-avatar--${(index % 4) + 1}`}>
                {message.authorName.charAt(0).toUpperCase()}
              </span>

              <div className="message-content">
                {message.parentId && (
                  <div className="reply-reference">
                    <CornerUpLeft size={13} />
                    <span>
                      {message.parentPreview || `メッセージ ${message.parentId} への返信`}
                    </span>
                  </div>
                )}

                <header>
                  <div>
                    <strong>{message.authorName}</strong>
                    <time>{formatDate(message.createdAt)}</time>
                    {message.updatedAt &&
                      message.updatedAt !== message.createdAt && <small>編集済み</small>}
                  </div>

                  {!message.isDeleted && (
                    <div className="message-actions">
                      <button
                        type="button"
                        title="返信"
                        onClick={() => setReplyTarget(message)}
                      >
                        <CornerUpLeft size={15} />
                      </button>

                      <button
                        type="button"
                        title="編集"
                        onClick={() => {
                          setEditingId(message.id);
                          setEditingText(message.content);
                        }}
                      >
                        <Edit3 size={15} />
                      </button>

                      <button
                        type="button"
                        title="削除"
                        onClick={() => void handleDelete(message.id)}
                      >
                        <Trash2 size={15} />
                      </button>

                      <button type="button" title="その他">
                        <MoreHorizontal size={15} />
                      </button>
                    </div>
                  )}
                </header>

                {editingId !== null &&
                String(editingId) === String(message.id) ? (
                  <div className="message-edit">
                    <textarea
                      value={editingText}
                      onChange={(event) => setEditingText(event.target.value)}
                      rows={3}
                    />

                    <div>
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={() => {
                          setEditingId(null);
                          setEditingText("");
                        }}
                      >
                        キャンセル
                      </button>

                      <button
                        type="button"
                        className="primary-button"
                        onClick={() => void handleEdit(message.id)}
                      >
                        保存
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className={message.isDeleted ? "deleted-message" : undefined}>
                    {message.isDeleted
                      ? "このメッセージは削除されました。"
                      : message.content}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <form className="message-composer" onSubmit={handleSubmit}>
        {replyTarget && (
          <div className="reply-banner">
            <CornerUpLeft size={15} />
            <span>
              <strong>{replyTarget.authorName}</strong> に返信
            </span>
            <button type="button" onClick={() => setReplyTarget(null)}>
              <X size={16} />
            </button>
          </div>
        )}

        <textarea
          value={messageText}
          onChange={(event) => setMessageText(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
          placeholder={`${channel?.name ?? "チャンネル"}にメッセージを送信`}
          disabled={isSending}
        />

        <footer>
          <span>Enterで送信・Shift + Enterで改行</span>

          <button
            type="submit"
            className="primary-button"
            disabled={isSending || !messageText.trim()}
          >
            <Send size={15} />
            {isSending ? "送信中..." : "送信"}
          </button>
        </footer>
      </form>
    </div>
  );
}

function MessageEmptyIcon() {
  return (
    <span className="message-empty-icon" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  );
}

export default ChannelPage;
