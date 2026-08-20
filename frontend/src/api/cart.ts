import { apiClient } from "@/lib/apiClient";
import { newIdempotencyKey } from "@/lib/idempotency";
import type { CartSummary } from "@/api/types";

export async function fetchCart(): Promise<CartSummary> {
  const { data } = await apiClient.get<CartSummary>("/cart");
  return data;
}

export async function addCartItem(productId: string, quantity: number): Promise<CartSummary> {
  const { data } = await apiClient.post<CartSummary>(
    "/cart/items",
    { product_id: productId, quantity },
    { headers: { "Idempotency-Key": newIdempotencyKey() } },
  );
  return data;
}

export async function updateCartItem(productId: string, quantity: number): Promise<CartSummary> {
  const { data } = await apiClient.patch<CartSummary>(`/cart/items/${productId}`, { quantity });
  return data;
}

export async function removeCartItem(productId: string): Promise<void> {
  await apiClient.delete(`/cart/items/${productId}`);
}

export async function clearCart(): Promise<void> {
  await apiClient.delete("/cart");
}
