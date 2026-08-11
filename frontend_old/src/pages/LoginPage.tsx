import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router";

function LoginPage() {
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    navigate("/app");
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-logo">C</div>

        <h1>Codagora</h1>
        <p className="auth-description">
          チームの開発とコミュニケーションをひとつの場所に。
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            メールアドレス
            <input
              type="email"
              name="email"
              placeholder="example@codagora.com"
              required
            />
          </label>

          <label>
            パスワード
            <input
              type="password"
              name="password"
              placeholder="パスワードを入力"
              required
            />
          </label>

          <button type="submit">ログイン</button>
        </form>

        <p className="auth-footer">
          アカウントを持っていませんか？
          <Link to="/register">新規登録</Link>
        </p>
      </section>
    </main>
  );
}

export default LoginPage;