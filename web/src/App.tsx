import { useEffect, useState } from "react";
import "./App.css";
import { getHealth, type HealthResponse } from "./services/api";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const result = await getHealth();
        setHealth(result);
      } catch (caughtError) {
        const message =
          caughtError instanceof Error
            ? caughtError.message
            : "不明なエラーが発生しました。";

        setError(message);
      }
    };

    void loadHealth();
  }, []);

  return (
    <main className="app">
      <section className="status-card">
        <p className="eyebrow">CODAGORA</p>
        <h1>開発が集まる、チームの広場。</h1>

        {!health && !error && <p>APIに接続しています...</p>}

        {health && (
          <div className="status">
            <span className="status-dot" />
            <div>
              <strong>バックエンド接続成功</strong>
              <p>{health.message}</p>
            </div>
          </div>
        )}

        {error && <p className="error">接続エラー：{error}</p>}
      </section>
    </main>
  );
}

export default App;