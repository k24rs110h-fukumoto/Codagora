import {
    useEffect,
    useMemo,
    useState,
    type FormEvent,
} from "react";
import { useParams } from "react-router";
import { getApiErrorMessage } from "../lib/getApiErrorMessage";
import {
    createMessage,
    getMessages,
} from "../services/messageService";
import type {
    Message,
    MessageAuthor,
} from "../types/api";

function getAuthorName(
    author: MessageAuthor,
    authorName?: string | null,
): string {
    if (authorName) {
        return authorName;
    }

    if (typeof author === "string") {
        return author;
    }

    if (!author) {
        return "削除済みユーザー";
    }

    return (
        author.display_name ||
        author.username ||
        author.email ||
        "ユーザー"
    );
}

function formatMessageDate(dateValue: string): string {
    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return dateValue;
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

    const [messages, setMessages] = useState<Message[]>([]);
    const [messageText, setMessageText] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const channelDisplayName = useMemo(() => {
        return channelId ?? "unknown-channel";
    }, [channelId]);

    useEffect(() => {
        if (!workspaceSlug || !channelId) {
            return;
        }

        const currentWorkspaceSlug = workspaceSlug;
        const currentChannelId = channelId;
        const controller = new AbortController();

        async function loadMessages() {
            try {
                setIsLoading(true);
                setErrorMessage("");

                const messageList = await getMessages(
                    currentWorkspaceSlug,
                    currentChannelId,
                    controller.signal,
                );

                setMessages(messageList);
            } catch (error) {
                if (controller.signal.aborted) {
                    return;
                }

                setErrorMessage(
                    getApiErrorMessage(
                        error,
                        "メッセージの取得に失敗しました。",
                    ),
                );
            } finally {
                if (!controller.signal.aborted) {
                    setIsLoading(false);
                }
            }
        }

        void loadMessages();

        return () => {
            controller.abort();
        };
    }, [workspaceSlug, channelId]);

    async function handleSubmit(
        event: FormEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        if (!workspaceSlug || !channelId || isSending) {
            return;
        }

        const currentWorkspaceSlug = workspaceSlug;
        const currentChannelId = channelId;
        const content = messageText.trim();

        if (!content) {
            return;
        }

        try {
            setIsSending(true);
            setErrorMessage("");

            const createdMessage = await createMessage(
                currentWorkspaceSlug,
                currentChannelId,
                {
                    content,
                },
            );

            setMessages((currentMessages) => [
                ...currentMessages,
                createdMessage,
            ]);

            setMessageText("");
        } catch (error) {
            setErrorMessage(
                getApiErrorMessage(
                    error,
                    "メッセージの送信に失敗しました。",
                ),
            );
        } finally {
            setIsSending(false);
        }
    }

    if (!workspaceSlug || !channelId) {
        return (
            <section className="channel-page-error">
                チャンネル情報が指定されていません。
            </section>
        );
    }

    return (
        <section className="channel-page">
            <header className="channel-header">
                <div>
                    <span className="channel-header-symbol">
                        #
                    </span>

                    <strong>{channelDisplayName}</strong>
                </div>

                <div className="channel-header-actions">
                    <button type="button">検索</button>
                </div>
            </header>

            <div className="message-list">
                <div className="channel-start">
                    <div className="channel-start-icon">#</div>

                    <h1>
                        #{channelDisplayName}へようこそ！
                    </h1>

                    <p>このチャンネルの始まりです。</p>
                </div>

                {isLoading && (
                    <div className="message-status">
                        メッセージを読み込んでいます...
                    </div>
                )}

                {errorMessage && (
                    <div className="message-error">
                        {errorMessage}
                    </div>
                )}

                {!isLoading &&
                    !errorMessage &&
                    messages.length === 0 && (
                        <div className="message-status">
                            まだメッセージはありません。
                        </div>
                    )}

                {messages.map((message) => {
                    const authorName = getAuthorName(
                        message.author,
                        message.author_name,
                    );

                    return (
                        <article
                            key={message.id}
                            className="message-item"
                        >
                            <div className="message-avatar">
                                {authorName.charAt(0).toUpperCase()}
                            </div>

                            <div className="message-body">
                                <div className="message-meta">
                                    <strong>{authorName}</strong>

                                    <time>
                                        {formatMessageDate(
                                            message.created_at,
                                        )}
                                    </time>
                                </div>

                                <p
                                    className={
                                        message.is_deleted
                                            ? "message-content--deleted"
                                            : undefined
                                    }
                                >
                                    {message.is_deleted
                                        ? "このメッセージは削除されました。"
                                        : message.content}
                                </p>
                            </div>
                        </article>
                    );
                })}
            </div>

            <form
                className="message-composer"
                onSubmit={handleSubmit}
            >
                <button
                    type="button"
                    className="message-add-button"
                    aria-label="ファイルを追加"
                >
                    +
                </button>

                <input
                    type="text"
                    value={messageText}
                    onChange={(event) =>
                        setMessageText(event.target.value)
                    }
                    placeholder={`#${channelDisplayName}へメッセージを送信`}
                    disabled={isSending}
                />

                <button
                    type="submit"
                    className="message-send-button"
                    disabled={
                        isSending || messageText.trim().length === 0
                    }
                >
                    {isSending ? "送信中" : "送信"}
                </button>
            </form>
        </section>
    );
}

export default ChannelPage;