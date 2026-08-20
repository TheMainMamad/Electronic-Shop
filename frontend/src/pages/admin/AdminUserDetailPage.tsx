import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminCreditWallet, adminDebitWallet, fetchAdminUser, fetchAdminWallet, updateAdminUser } from "@/api/admin";
import type { UserRole } from "@/api/types";
import { formatJalaliDateTime, formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { userRoleLabels } from "@/lib/statusLabels";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";

export function AdminUserDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const push = useToastStore((state) => state.push);
  const [walletAmount, setWalletAmount] = useState("");
  const [walletReason, setWalletReason] = useState("");

  const user = useQuery({ queryKey: ["admin", "users", id], queryFn: () => fetchAdminUser(id) });
  const wallet = useQuery({ queryKey: ["admin", "wallets", id], queryFn: () => fetchAdminWallet(id) });

  const updateUser = useMutation({
    mutationFn: (payload: { role?: UserRole; is_active?: boolean }) => updateAdminUser(id, payload),
    onSuccess: () => {
      push("اطلاعات کاربر به‌روزرسانی شد.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin", "users", id] });
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const creditWallet = useMutation({
    mutationFn: () => adminCreditWallet(id, walletAmount, walletReason),
    onSuccess: () => {
      push("موجودی کیف پول افزایش یافت.", "success");
      setWalletAmount("");
      setWalletReason("");
      queryClient.invalidateQueries({ queryKey: ["admin", "wallets", id] });
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const debitWallet = useMutation({
    mutationFn: () => adminDebitWallet(id, walletAmount, walletReason),
    onSuccess: () => {
      push("موجودی کیف پول کاهش یافت.", "success");
      setWalletAmount("");
      setWalletReason("");
      queryClient.invalidateQueries({ queryKey: ["admin", "wallets", id] });
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  if (user.isLoading) return <Spinner />;
  if (user.isError || !user.data) return <ErrorState message={getErrorMessage(user.error, "کاربر پیدا نشد.")} />;

  const data = user.data;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">جزئیات کاربر</h1>

      <Card>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <dt className="text-gray-500">نام کاربری</dt>
          <dd className="ltr-inline">{data.username}</dd>
          <dt className="text-gray-500">ایمیل</dt>
          <dd className="ltr-inline">{data.email}</dd>
          <dt className="text-gray-500">تاریخ عضویت</dt>
          <dd>{formatJalaliDateTime(data.created_at)}</dd>
          <dt className="text-gray-500">آخرین ورود</dt>
          <dd>{data.last_login ? formatJalaliDateTime(data.last_login) : "—"}</dd>
        </dl>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <Select
            label="نقش"
            value={data.role}
            onChange={(event) => updateUser.mutate({ role: event.target.value as UserRole })}
          >
            {Object.entries(userRoleLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          <Button
            variant={data.is_active ? "danger" : "secondary"}
            onClick={() => updateUser.mutate({ is_active: !data.is_active })}
          >
            {data.is_active ? "غیرفعال‌سازی حساب" : "فعال‌سازی حساب"}
          </Button>
          <Badge tone={data.is_active ? "success" : "danger"}>{data.is_active ? "فعال" : "غیرفعال"}</Badge>
        </div>
      </Card>

      <Card>
        <h2 className="mb-3 font-bold">کیف پول</h2>
        <p className="mb-3 text-lg font-bold">{wallet.data ? formatToman(wallet.data.balance) : "—"}</p>
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(event) => event.preventDefault()}
        >
          <Input label="مبلغ" type="number" min={1} value={walletAmount} onChange={(e) => setWalletAmount(e.target.value)} />
          <Input label="دلیل" value={walletReason} onChange={(e) => setWalletReason(e.target.value)} />
          <Button
            type="button"
            variant="secondary"
            loading={creditWallet.isPending}
            disabled={!walletAmount || !walletReason}
            onClick={() => creditWallet.mutate()}
          >
            افزایش موجودی
          </Button>
          <Button
            type="button"
            variant="danger"
            loading={debitWallet.isPending}
            disabled={!walletAmount || !walletReason}
            onClick={() => debitWallet.mutate()}
          >
            کاهش موجودی
          </Button>
        </form>
      </Card>
    </div>
  );
}
