export interface HealthResponse {
  status: string;
  service: string;
  message: string;
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (!apiBaseUrl) {
  throw new Error("VITE_API_BASE_URL is not configured.");
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/health/`);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}