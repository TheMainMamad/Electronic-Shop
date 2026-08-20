import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchAdminReport } from "@/api/admin";
import { formatToman } from "@/lib/persian";
import { orderStatusLabels, ticketStatusLabels } from "@/lib/statusLabels";
import { StatCard } from "@/components/admin/StatCard";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";

type RangeOption = "today" | "7d" | "30d" | "custom";

const RANGE_LABELS: Record<RangeOption, string> = {
  today: "امروز",
  "7d": "۷ روز اخیر",
  "30d": "۳۰ روز اخیر",
  custom: "بازه سفارشی",
};

export function AdminReportsPage() {
  const [range, setRange] = useState<RangeOption>("7d");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const report = useQuery({
    queryKey: ["admin", "reports", range, startDate, endDate],
    queryFn: () => fetchAdminReport(range, startDate || undefined, endDate || undefined),
    enabled: range !== "custom" || Boolean(startDate && endDate),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">گزارش‌ها</h1>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <Select label="بازه زمانی" value={range} onChange={(e) => setRange(e.target.value as RangeOption)}>
            {Object.entries(RANGE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          {range === "custom" && (
            <>
              <Input label="از تاریخ" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              <Input label="تا تاریخ" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </>
          )}
        </div>
      </Card>

      {report.isLoading && <Spinner />}

      {report.data && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="تعداد سفارش‌ها" value={report.data.sales.order_count} />
            <StatCard label="فروش کل" formatted={formatToman(report.data.sales.total_revenue)} />
            <StatCard label="میانگین ارزش سفارش" formatted={formatToman(report.data.sales.average_order_value)} />
            <StatCard label="ثبت‌نام‌های جدید" value={report.data.users.new_registrations} />
            <StatCard label="محصولات فعال" value={report.data.products.total_active_products} />
            <StatCard label="موجودی کم" value={report.data.products.low_stock_count} />
            <StatCard label="ناموجود" value={report.data.products.out_of_stock_count} />
            <StatCard label="پرداخت‌های موفق" value={report.data.payments.verified_count} />
            <StatCard label="مبلغ پرداخت‌شده" formatted={formatToman(report.data.payments.verified_amount)} />
            <StatCard label="پرداخت‌های ناموفق" value={report.data.payments.failed_count} />
            <StatCard label="تیکت‌های بسته‌شده خودکار" value={report.data.tickets.auto_closed_count} />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <h2 className="mb-3 font-bold">وضعیت سفارش‌ها</h2>
              <ul className="flex flex-col gap-1 text-sm">
                {report.data.orders.by_status.map((row) => (
                  <li key={row.label} className="flex justify-between">
                    <span>{orderStatusLabels[row.label] ?? row.label}</span>
                    <span>{row.count}</span>
                  </li>
                ))}
              </ul>
            </Card>
            <Card>
              <h2 className="mb-3 font-bold">وضعیت تیکت‌ها</h2>
              <ul className="flex flex-col gap-1 text-sm">
                {report.data.tickets.by_status.map((row) => (
                  <li key={row.label} className="flex justify-between">
                    <span>{ticketStatusLabels[row.label] ?? row.label}</span>
                    <span>{row.count}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          <Card>
            <h2 className="mb-3 font-bold">عملکرد دسته‌بندی‌ها</h2>
            <table className="w-full text-sm">
              <thead className="text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="py-1 text-right">دسته‌بندی</th>
                  <th className="py-1 text-right">تعداد اقلام فروخته‌شده</th>
                  <th className="py-1 text-right">درآمد</th>
                </tr>
              </thead>
              <tbody>
                {report.data.category_performance.map((row) => (
                  <tr key={row.category_name} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="py-1.5">{row.category_name}</td>
                    <td className="py-1.5">{row.order_item_count}</td>
                    <td className="py-1.5">{formatToman(row.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}
