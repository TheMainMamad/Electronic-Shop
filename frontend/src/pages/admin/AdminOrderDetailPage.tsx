import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchOrder } from "@/api/orders";
import { updateOrderStatus } from "@/api/admin";
import type { OrderStatus } from "@/api/types";
import { formatJalaliDateTime, formatToman } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { orderStatusLabels, statusTone } from "@/lib/statusLabels";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";

const ALL_STATUSES: OrderStatus[] = [
  "pending",
  "awaiting_payment",
  "paid",
  "processing",
  "shipped",
  "completed",
  "cancelled",
  "payment_failed",
  "refunded",
];

export function AdminOrderDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const push = useToastStore((state) => state.push);
  const [nextStatus, setNextStatus] = useState<OrderStatus | "">("");

  const order = useQuery({ queryKey: ["orders", "detail", id], queryFn: () => fetchOrder(id) });

  const updateStatus = useMutation({
    mutationFn: () => updateOrderStatus(id, nextStatus as OrderStatus),
    onSuccess: () => {
      push("وضعیت سفارش به‌روزرسانی شد.", "success");
      setNextStatus("");
      queryClient.invalidateQueries({ queryKey: ["orders", "detail", id] });
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  if (order.isLoading) return <Spinner />;
  if (order.isError || !order.data) return <ErrorState message={getErrorMessage(order.error, "سفارش پیدا نشد.")} />;

  const data = order.data;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">جزئیات سفارش</h1>
          <span className="ltr-inline text-xs text-gray-400">{data.id}</span>
        </div>
        <Badge tone={statusTone(data.status)}>{orderStatusLabels[data.status]}</Badge>
      </div>

      <Card>
        <h2 className="mb-3 font-bold">اقلام سفارش</h2>
        <table className="w-full text-sm">
          <thead className="text-gray-500 dark:text-gray-400">
            <tr>
              <th className="py-1 text-right">نام کالا</th>
              <th className="py-1 text-right">SKU</th>
              <th className="py-1 text-right">تعداد</th>
              <th className="py-1 text-right">قیمت واحد</th>
              <th className="py-1 text-right">جمع</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item, index) => (
              <tr key={index} className="border-t border-gray-100 dark:border-gray-800">
                <td className="py-1.5">{item.product_name}</td>
                <td className="ltr-inline py-1.5 text-xs text-gray-500">{item.sku}</td>
                <td className="py-1.5">{item.quantity}</td>
                <td className="py-1.5">{formatToman(item.unit_price)}</td>
                <td className="py-1.5">{formatToman(item.subtotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-3 flex justify-between border-t border-gray-100 pt-3 font-bold dark:border-gray-800">
          <span>مبلغ کل</span>
          <span>{formatToman(data.total)}</span>
        </div>
      </Card>

      {data.shipping_address && (
        <Card>
          <h2 className="mb-2 font-bold">آدرس ارسال</h2>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {data.shipping_address.recipient_name} — {data.shipping_address.province}، {data.shipping_address.city}،{" "}
            {data.shipping_address.address_line}
          </p>
          <p className="ltr-inline mt-1 text-xs text-gray-400">{data.shipping_address.phone_number}</p>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 font-bold">تغییر وضعیت سفارش</h2>
        <div className="flex flex-wrap items-end gap-2">
          <Select label="وضعیت جدید" value={nextStatus} onChange={(e) => setNextStatus(e.target.value as OrderStatus)}>
            <option value="">انتخاب کنید</option>
            {ALL_STATUSES.map((status) => (
              <option key={status} value={status}>
                {orderStatusLabels[status]}
              </option>
            ))}
          </Select>
          <Button disabled={!nextStatus} loading={updateStatus.isPending} onClick={() => updateStatus.mutate()}>
            اعمال تغییر
          </Button>
        </div>
      </Card>

      <p className="text-xs text-gray-400">ثبت‌شده در {formatJalaliDateTime(data.created_at)}</p>
    </div>
  );
}
