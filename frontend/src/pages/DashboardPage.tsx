import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useCurrentUser } from "@/hooks/useAuth";
import { useCart } from "@/hooks/useCart";
import { fetchMyOrders } from "@/api/orders";
import { fetchMyWallet } from "@/api/wallet";
import { fetchMyTickets } from "@/api/tickets";
import { formatToman } from "@/lib/persian";
import { orderStatusLabels, statusTone, ticketStatusLabels } from "@/lib/statusLabels";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

export function DashboardPage() {
  const { data: user } = useCurrentUser();
  const cart = useCart();
  const orders = useQuery({ queryKey: ["orders", "list", 1], queryFn: () => fetchMyOrders(1, 5) });
  const wallet = useQuery({ queryKey: ["wallet", "me"], queryFn: fetchMyWallet });
  const tickets = useQuery({ queryKey: ["tickets", "list", 1], queryFn: () => fetchMyTickets(1, 5) });

  if (!user) return <Spinner />;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">
        سلام {user.first_name || user.username}، خوش آمدید
      </h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-gray-500">موجودی کیف پول</p>
          <p className="mt-1 text-lg font-bold">{wallet.data ? formatToman(wallet.data.balance) : "—"}</p>
          <Link to="/wallet" className="mt-2 block text-xs text-brand-600 hover:underline">
            مشاهده کیف پول
          </Link>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">اقلام سبد خرید</p>
          <p className="mt-1 text-lg font-bold">{cart.data?.items.length ?? 0}</p>
          <Link to="/cart" className="mt-2 block text-xs text-brand-600 hover:underline">
            مشاهده سبد خرید
          </Link>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">تیکت‌های باز</p>
          <p className="mt-1 text-lg font-bold">
            {tickets.data?.items.filter((t) => t.status !== "closed").length ?? 0}
          </p>
          <Link to="/tickets" className="mt-2 block text-xs text-brand-600 hover:underline">
            مشاهده تیکت‌ها
          </Link>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">سفارش‌های اخیر</p>
          <p className="mt-1 text-lg font-bold">{orders.data?.total ?? 0}</p>
          <Link to="/orders" className="mt-2 block text-xs text-brand-600 hover:underline">
            مشاهده سفارش‌ها
          </Link>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 font-bold">سفارش‌های اخیر</h2>
          {orders.isLoading && <Spinner />}
          {orders.data && orders.data.items.length === 0 && (
            <p className="text-sm text-gray-500">هنوز سفارشی ثبت نکرده‌اید.</p>
          )}
          <ul className="flex flex-col gap-2">
            {orders.data?.items.map((order) => (
              <li key={order.id}>
                <Link
                  to={`/orders/${order.id}`}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <span className="ltr-inline text-xs text-gray-400">{order.id.slice(0, 8)}</span>
                  <Badge tone={statusTone(order.status)}>{orderStatusLabels[order.status]}</Badge>
                  <span>{formatToman(order.total)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <h2 className="mb-3 font-bold">تیکت‌های اخیر</h2>
          {tickets.isLoading && <Spinner />}
          {tickets.data && tickets.data.items.length === 0 && (
            <p className="text-sm text-gray-500">تیکت جدیدی ندارید.</p>
          )}
          <ul className="flex flex-col gap-2">
            {tickets.data?.items.map((ticket) => (
              <li key={ticket.id}>
                <Link
                  to={`/tickets/${ticket.id}`}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <span className="line-clamp-1">{ticket.subject}</span>
                  <Badge tone={statusTone(ticket.status)}>{ticketStatusLabels[ticket.status]}</Badge>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
