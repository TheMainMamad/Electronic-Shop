import { isAxiosError } from "axios";
import type { ApiErrorBody } from "@/api/types";

export function getErrorMessage(error: unknown, fallback = "خطایی رخ داد. لطفاً دوباره تلاش کنید."): string {
  if (isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data?.error?.message ?? fallback;
  }
  return fallback;
}
