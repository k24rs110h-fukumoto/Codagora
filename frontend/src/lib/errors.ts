import axios from "axios";

type ErrorPayload = {
  detail?: string;
  message?: string;
  non_field_errors?: string[];
  [key: string]: unknown;
};

export function getErrorMessage(
  error: unknown,
  fallback = "処理に失敗しました。",
): string {
  if (!axios.isAxiosError<ErrorPayload>(error)) {
    return fallback;
  }

  const data = error.response?.data;

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (typeof data?.message === "string") {
    return data.message;
  }

  if (Array.isArray(data?.non_field_errors)) {
    return data.non_field_errors.join("\n");
  }

  if (data && typeof data === "object") {
    for (const value of Object.values(data)) {
      if (typeof value === "string") {
        return value;
      }

      if (Array.isArray(value) && typeof value[0] === "string") {
        return value.join("\n");
      }
    }
  }

  return error.message || fallback;
}

export function isAuthenticationError(error: unknown): boolean {
  return (
    axios.isAxiosError(error) &&
    (error.response?.status === 401 || error.response?.status === 403)
  );
}
