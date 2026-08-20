import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { depositToWallet, fetchMyWallet, fetchMyWalletTransactions } from "@/api/wallet";
import { formatJalaliDateTime, formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { walletTransactionTypeLabels } from "@/lib/statusLabels";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function WalletPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");
  const [amount, setAmount] = useState("");
  const push = useToastStore((state) => state.push);
  const queryClient = useQueryClient();

  const wallet = useQuery({ queryKey: ["wallet", "me"], queryFn: fetchMyWallet });
  const transactions = useQuery({
    queryKey: ["wallet", "transactions", page],
    queryFn: () => fetchMyWalletTransactions(page, 10),
  });

  const deposit = useMutation({
    mutationFn: () => depositToWallet(amount),
    onSuccess: () => {
      push("موجودی کیف پول افزایش یافت.", "success");
      setAmount("");
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">کیف پول</h1>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <p className="text-sm text-gray-500">موجودی فعلی</p>
          <p className="mt-1 text-2xl font-bold text-brand-700 dark:text-brand-500">
            {wallet.data ? formatToman(wallet.data.balance) : "—"}
          </p>
        </Card>

        <Card>
          <h2 className="mb-2 font-bold">افزایش موجودی</h2>
          <form
            className="flex items-end gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              deposit.mutate();
            }}
          >
            <Input
              label="مبلغ (تومان)"
              type="number"
              min={1000}
              required
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              className="flex-1"
            />
            <Button type="submit" loading={deposit.isPending}>
              افزایش موجودی
            </Button>
          </form>
        </Card>
      </div>

      <div>
        <h2 className="mb-3 font-bold">تراکنش‌های کیف پول</h2>
        {transactions.isLoading && <Spinner />}
        {transactions.data && transactions.data.items.length === 0 && (
          <EmptyState title="هنوز تراکنشی ثبت نشده است." />
        )}
        {transactions.data && transactions.data.items.length > 0 && (
          <>
            <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                  <tr>
                    <th className="px-3 py-2 text-right">نوع</th>
                    <th className="px-3 py-2 text-right">مبلغ</th>
                    <th className="px-3 py-2 text-right">موجودی پس از تراکنش</th>
                    <th className="px-3 py-2 text-right">تاریخ</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.data.items.map((tx) => (
                    <tr key={tx.id} className="border-t border-gray-100 dark:border-gray-800">
                      <td className="px-3 py-2">{walletTransactionTypeLabels[tx.type]}</td>
                      <td className="px-3 py-2">{formatToman(tx.amount)}</td>
                      <td className="px-3 py-2">{formatToman(tx.balance_after)}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">{formatJalaliDateTime(tx.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={transactions.data.page}
              totalPages={transactions.data.total_pages}
              onPageChange={(nextPage) => setSearchParams({ page: String(nextPage) })}
            />
          </>
        )}
      </div>
    </div>
  );
}
