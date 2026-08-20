import { apiClient } from "@/lib/apiClient";
import { newIdempotencyKey } from "@/lib/idempotency";
import type { Order, Page, ShippingAddress } from "@/api/types";

export async function checkout(shippingAddress?: ShippingAddress): Promise<Order> {
  const { data } = await apiClient.post<Order>(
    "/orders",
    { shipping_address: shippingAddress ?? null },
    { headers: { "Idempotency-Key": newIdempotencyKey() } },
  );
  return data;
}

export async function fetchMyOrders(page: number, pageSize = 10): Promise<Page<Order>> {
  const { data } = await apiClient.get<Page<Order>>("/orders", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function fetchOrder(orderId: string): Promise<Order> {
  const { data } = await apiClient.get<Order>(`/orders/${orderId}`);
  return data;
}

export async function cancelOrder(orderId: string): Promise<Order> {
  const { data } = await apiClient.post<Order>(`/orders/${orderId}/cancel`);
  return data;
}
