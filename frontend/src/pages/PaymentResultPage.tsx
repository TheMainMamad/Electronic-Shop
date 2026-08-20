import { Link, useSearchParams } from "react-router-dom";

import { useQuery } from "@tanstack/react-query";
import { fetchOrder } from "@/api/orders";
import { formatToman } from "@/lib/persian";
import { Spinner } from "@/components/ui/Spinner";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function PaymentResultPage() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get("order_id") ?? "";
  const status = searchParams.get("status");
  const succeeded = status === "paid";

  const order = useQuery({
    queryKey: ["orders", "detail", orderId],
    queryFn: () => fetchOrder(orderId),
    enabled: Boolean(orderId),
  });

  return (
    <div className="mx-auto max-w-md py-10">
      <Card className="text-center">
        <div
          className={`mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full text-2xl ${
            succeeded
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40"
              : "bg-red-100 text-red-700 dark:bg-red-900/40"
          }`}
        >
          {succeeded ? "✓" : "✕"}
        </div>
        <h1 className="text-lg font-bold">
          {succeeded ? "پرداخت با موفقیت انجام شد" : "پرداخت انجام نشد"}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {succeeded
            ? "سفارش شما ثبت شد و به‌زودی پردازش می‌شود."
            : "پرداخت شما ناموفق بود یا لغو شد. می‌توانید دوباره تلاش کنید."}
        </p>

        {order.isLoading && <Spinner />}
        {order.data && (
          <div className="mt-4 rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-800">
            <div className="flex justify-between">
              <span>شماره سفارش</span>
              <span className="ltr-inline">{order.data.id.slice(0, 8)}</span>
            </div>
            <div className="mt-1 flex justify-between font-bold">
              <span>مبلغ</span>
              <span>{formatToman(order.data.total)}</span>
            </div>
          </div>
        )}

        <div className="mt-5 flex flex-col gap-2">
          {orderId && (
            <Link to={`/orders/${orderId}`}>
              <Button className="w-full">مشاهده جزئیات سفارش</Button>
            </Link>
          )}
          <Link to="/products">
            <Button variant="secondary" className="w-full">
              ادامه خرید
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
