import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router";

function RegisterPage() {
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    navigate("/app");
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-logo">C</div>

        <h1>アカウント作成</h1>
        <p className="auth-description">
          Codagoraでチーム開発を始めましょう。
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            ユーザー名
            <input
              type="text"
              name="username"
              placeholder="Haruto"
              required
            />
          </label>

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
              placeholder="8文字以上"
              required
            />
          </label>

          <button type="submit">アカウントを作成</button>
        </form>

        <p className="auth-footer">
          すでにアカウントを持っていますか？
          <Link to="/login">ログイン</Link>
        </p>
      </section>
    </main>
  );
}

export default RegisterPage;