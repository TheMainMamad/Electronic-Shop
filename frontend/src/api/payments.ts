import { apiClient } from "@/lib/apiClient";
import { newIdempotencyKey } from "@/lib/idempotency";

export interface PaymentInitResponse {
  payment_id: string;
  payment_url: string;
}

export async function initPayment(orderId: string): Promise<PaymentInitResponse> {
  const { data } = await apiClient.post<PaymentInitResponse>(
    "/payments",
    { order_id: orderId },
    { headers: { "Idempotency-Key": newIdempotencyKey() } },
  );
  return data;
}
