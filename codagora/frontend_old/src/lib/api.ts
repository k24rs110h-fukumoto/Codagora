import axios from "axios";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem(
    "codagora_access_token",
  );

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

export default api;