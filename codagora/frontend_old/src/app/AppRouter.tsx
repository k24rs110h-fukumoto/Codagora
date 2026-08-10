import { Navigate, Route, Routes } from "react-router";
import WorkspaceLayout from "../components/layout/WorkspaceLayout";
import ChannelPage from "../pages/ChannelPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import RegisterPage from "../pages/RegisterPage";
import WorkspaceHomePage from "../pages/WorkspaceHomePage";
import WorkspaceSelectPage from "../pages/WorkspaceSelectPage";

function AppRouter() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />

      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/register"
        element={<RegisterPage />}
      />

      <Route
        path="/app"
        element={<WorkspaceSelectPage />}
      />

      <Route
        path="/app/workspaces/:workspaceSlug"
        element={<WorkspaceLayout />}
      >
        <Route index element={<WorkspaceHomePage />} />

        <Route
          path="channels/:channelId"
          element={<ChannelPage />}
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default AppRouter;