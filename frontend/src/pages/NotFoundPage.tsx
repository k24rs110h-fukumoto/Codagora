import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import Logo from "../components/Logo";

function NotFoundPage() {
  return (
    <main className="center-state">
      <Logo />
      <span className="not-found-code">404</span>
      <h1>ページが見つかりません</h1>
      <p>URLが変更されたか、ページが削除された可能性があります。</p>
      <Link to="/" className="primary-button">
        <ArrowLeft size={16} />
        ワークスペース一覧へ
      </Link>
    </main>
  );
}

export default NotFoundPage;
