import { apiClient } from "@/lib/apiClient";
import { newIdempotencyKey } from "@/lib/idempotency";
import type { Page, Wallet, WalletTransaction } from "@/api/types";

export async function fetchMyWallet(): Promise<Wallet> {
  const { data } = await apiClient.get<Wallet>("/wallet");
  return data;
}

export async function fetchMyWalletTransactions(page: number, pageSize = 10): Promise<Page<WalletTransaction>> {
  const { data } = await apiClient.get<Page<WalletTransaction>>("/wallet/transactions", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function depositToWallet(amount: string): Promise<WalletTransaction> {
  const { data } = await apiClient.post<WalletTransaction>(
    "/wallet/deposit",
    { amount },
    { headers: { "Idempotency-Key": newIdempotencyKey() } },
  );
  return data;
}
