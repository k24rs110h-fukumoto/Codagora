import { Link } from "react-router";

function NotFoundPage() {
  return (
    <main className="not-found-page">
      <p>404</p>
      <h1>ページが見つかりません</h1>
      <Link to="/app">Codagoraへ戻る</Link>
    </main>
  );
}

export default NotFoundPage;