import { Navigate, Route, Routes } from "react-router-dom";
import SessionGate from "./components/SessionGate";
import WorkspaceLayout from "./layouts/WorkspaceLayout";
import ChannelPage from "./pages/ChannelPage";
import NotFoundPage from "./pages/NotFoundPage";
import WorkspaceListPage from "./pages/WorkspaceListPage";
import WorkspaceOverviewPage from "./pages/WorkspaceOverviewPage";

function App() {
  return (
    <SessionGate>
      <Routes>
        <Route path="/" element={<WorkspaceListPage />} />

        <Route
          path="/workspaces/:workspaceSlug"
          element={<WorkspaceLayout />}
        >
          <Route index element={<WorkspaceOverviewPage />} />

          <Route
            path="channels/:channelId"
            element={<ChannelPage />}
          />
        </Route>

        <Route
          path="/app"
          element={<Navigate to="/" replace />}
        />

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </SessionGate>
  );
}

export default App;