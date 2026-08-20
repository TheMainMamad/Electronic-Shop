import { useQuery } from "@tanstack/react-query";

import { fetchDashboardCharts, fetchDashboardStats } from "@/api/admin";
import { formatToman } from "@/lib/persian";
import { orderStatusLabels, paymentStatusLabels, ticketStatusLabels } from "@/lib/statusLabels";
import { StatCard } from "@/components/admin/StatCard";
import { TrendChartCard } from "@/components/admin/TrendChartCard";
import { DistributionChartCard } from "@/components/admin/DistributionChartCard";
import { Spinner } from "@/components/ui/Spinner";

export function AdminDashboardPage() {
  const stats = useQuery({ queryKey: ["admin", "dashboard", "stats"], queryFn: fetchDashboardStats });
  const charts = useQuery({ queryKey: ["admin", "dashboard", "charts"], queryFn: () => fetchDashboardCharts(14) });

  if (stats.isLoading || charts.isLoading) return <Spinner />;
  if (!stats.data || !charts.data) return null;

  const s = stats.data;
  const c = charts.data;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">داشبورد</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="کل کاربران" value={s.total_users} />
        <StatCard label="کاربران فعال" value={s.active_users} />
        <StatCard label="ثبت‌نام امروز" value={s.new_users_today} />
        <StatCard label="کل محصولات" value={s.total_products} />
        <StatCard label="موجودی کم" value={s.low_stock_products} />
        <StatCard label="ناموجود" value={s.out_of_stock_products} />
        <StatCard label="کل سفارش‌ها" value={s.total_orders} />
        <StatCard label="سفارش‌های امروز" value={s.orders_today} />
        <StatCard label="سفارش‌های در انتظار" value={s.pending_orders} />
        <StatCard label="سفارش‌های تکمیل‌شده" value={s.completed_orders} />
        <StatCard label="سفارش‌های لغوشده" value={s.cancelled_orders} />
        <StatCard label="پرداخت‌های موفق" value={s.successful_payments} />
        <StatCard label="پرداخت‌های ناموفق" value={s.failed_payments} />
        <StatCard label="فروش کل" formatted={formatToman(s.total_sales)} />
        <StatCard label="تراکنش‌های کیف پول" value={s.wallet_transactions} />
        <StatCard label="تیکت‌های باز" value={s.open_tickets} />
        <StatCard label="تیکت‌های بی‌پاسخ" value={s.unanswered_tickets} />
        <StatCard label="تیکت‌های بسته‌شده" value={s.closed_tickets} />
        <StatCard label="سبدهای فعال" value={s.active_carts} />
        <StatCard label="سبدهای رهاشده" value={s.abandoned_carts} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TrendChartCard title="سفارش‌ها در ۱۴ روز اخیر" data={c.orders_per_day} />
        <TrendChartCard
          title="فروش در ۱۴ روز اخیر"
          data={c.revenue_per_day.map((point) => ({ date: point.date, value: Number(point.value) }))}
          valueFormatter={(value) => formatToman(value)}
        />
        <TrendChartCard title="ثبت‌نام کاربران در ۱۴ روز اخیر" data={c.registrations_per_day} />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <DistributionChartCard
          title="وضعیت سفارش‌ها"
          data={c.order_status_distribution}
          labelMap={orderStatusLabels}
        />
        <DistributionChartCard
          title="وضعیت پرداخت‌ها"
          data={c.payment_status_distribution}
          labelMap={paymentStatusLabels}
        />
        <DistributionChartCard title="محصولات به تفکیک دسته‌بندی" data={c.products_by_category} />
        <DistributionChartCard
          title="وضعیت تیکت‌ها"
          data={c.ticket_status_distribution}
          labelMap={ticketStatusLabels}
        />
      </div>
    </div>
  );
}
