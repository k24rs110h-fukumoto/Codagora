import axios from "axios";

type ApiErrorData = {
  detail?: string;
  message?: string;
  non_field_errors?: string[];
};

export function getApiErrorMessage(
  error: unknown,
  fallbackMessage: string,
): string {
  if (!axios.isAxiosError<ApiErrorData>(error)) {
    return fallbackMessage;
  }

  const responseData = error.response?.data;

  if (responseData?.detail) {
    return responseData.detail;
  }

  if (responseData?.message) {
    return responseData.message;
  }

  if (
    responseData?.non_field_errors &&
    responseData.non_field_errors.length > 0
  ) {
    return responseData.non_field_errors.join("\n");
  }

  if (error.message) {
    return error.message;
  }

  return fallbackMessage;
}