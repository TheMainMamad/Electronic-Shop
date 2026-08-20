import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchMyOrders } from "@/api/orders";
import { formatJalaliDate, formatToman } from "@/lib/persian";
import { orderStatusLabels, statusTone } from "@/lib/statusLabels";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function OrdersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");
  const orders = useQuery({
    queryKey: ["orders", "list", page],
    queryFn: () => fetchMyOrders(page, 10),
  });

  if (orders.isLoading) return <Spinner />;
  if (!orders.data || orders.data.items.length === 0) {
    return <EmptyState title="سفارشی برای نمایش وجود ندارد." />;
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold">سفارش‌های من</h1>
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
            <tr>
              <th className="px-3 py-2 text-right">شماره سفارش</th>
              <th className="px-3 py-2 text-right">تاریخ</th>
              <th className="px-3 py-2 text-right">وضعیت</th>
              <th className="px-3 py-2 text-right">مبلغ</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {orders.data.items.map((order) => (
              <tr key={order.id} className="border-t border-gray-100 dark:border-gray-800">
                <td className="ltr-inline px-3 py-2 text-xs text-gray-500">{order.id.slice(0, 8)}</td>
                <td className="px-3 py-2">{formatJalaliDate(order.created_at)}</td>
                <td className="px-3 py-2">
                  <Badge tone={statusTone(order.status)}>{orderStatusLabels[order.status]}</Badge>
                </td>
                <td className="px-3 py-2">{formatToman(order.total)}</td>
                <td className="px-3 py-2">
                  <Link to={`/orders/${order.id}`} className="text-brand-600 hover:underline">
                    جزئیات
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        page={orders.data.page}
        totalPages={orders.data.total_pages}
        onPageChange={(nextPage) => setSearchParams({ page: String(nextPage) })}
      />
    </div>
  );
}
