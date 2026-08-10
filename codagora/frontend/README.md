# Codagora Frontend

CodagoraのDjango REST Frameworkバックエンドに接続する、React + TypeScriptフロントエンドです。

## 実装済み

- Django SessionAuthenticationでのログイン・ログアウト導線
- ワークスペース一覧・作成・招待コード参加
- ワークスペース概要
- メンバー一覧
- 招待コード発行
- チャンネル一覧・作成
- メッセージ一覧・投稿
- メッセージ返信
- メッセージ編集
- メッセージ削除（バックエンド側のソフトデリートAPIを利用）
- レスポンシブUI

## 開発起動

バックエンド:

```bash
cd backend
source .venv/bin/activate
python manage.py runserver 127.0.0.1:8000
```

フロントエンド:

```bash
cd frontend
npm install
npm run dev
```

ブラウザ:

```text
http://127.0.0.1:5173
```

## 認証

Viteの開発プロキシが `/api` と `/api-auth` をDjangoへ転送します。
そのため、開発中はCORS設定を変更せずにDjangoのセッションCookieを利用できます。

未ログインの場合は「Djangoでログイン」ボタンから `/api-auth/login/` を開きます。

## APIパス

APIパスは `src/services/codagoraApi.ts` にまとめています。

バックエンドのURL名が異なる場合は、以下の候補配列だけを修正してください。

- `joinWorkspace`
- `createInviteCode`

主要APIは次の構成を前提にしています。

```text
GET/POST /api/workspaces/
GET       /api/workspaces/:slug/members/
GET/POST  /api/workspaces/:slug/channels/
GET/POST  /api/workspaces/:slug/channels/:channelId/messages/
PATCH/DELETE /api/workspaces/:slug/channels/:channelId/messages/:messageId/
```
