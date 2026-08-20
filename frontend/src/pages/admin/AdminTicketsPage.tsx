import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchAdminTickets } from "@/api/admin";
import type { TicketStatus } from "@/api/types";
import { formatJalaliDateTime } from "@/lib/persian";
import { ticketPriorityLabels, ticketStatusLabels, statusTone } from "@/lib/statusLabels";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function AdminTicketsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");
  const status = (searchParams.get("status") as TicketStatus | null) ?? undefined;

  const tickets = useQuery({
    queryKey: ["admin", "tickets", page, status],
    queryFn: () => fetchAdminTickets(page, 20, status),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">تیکت‌ها</h1>
        <Select
          value={status ?? ""}
          onChange={(event) => {
            const next = new URLSearchParams(searchParams);
            if (event.target.value) next.set("status", event.target.value);
            else next.delete("status");
            next.set("page", "1");
            setSearchParams(next);
          }}
          className="w-56"
        >
          <option value="">همه وضعیت‌ها</option>
          {Object.entries(ticketStatusLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      </div>

      {tickets.isLoading && <Spinner />}
      {tickets.data && tickets.data.items.length === 0 && <EmptyState title="تیکتی ثبت نشده است." />}
      {tickets.data && tickets.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                <tr>
                  <th className="px-3 py-2 text-right">موضوع</th>
                  <th className="px-3 py-2 text-right">اولویت</th>
                  <th className="px-3 py-2 text-right">وضعیت</th>
                  <th className="px-3 py-2 text-right">آخرین به‌روزرسانی</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {tickets.data.items.map((ticket) => (
                  <tr key={ticket.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="px-3 py-2">{ticket.subject}</td>
                    <td className="px-3 py-2">{ticketPriorityLabels[ticket.priority]}</td>
                    <td className="px-3 py-2">
                      <Badge tone={statusTone(ticket.status)}>{ticketStatusLabels[ticket.status]}</Badge>
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {formatJalaliDateTime(ticket.last_response_at)}
                    </td>
                    <td className="px-3 py-2">
                      <Link to={`/admin/tickets/${ticket.id}`} className="text-brand-600 hover:underline">
                        مشاهده
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={tickets.data.page}
            totalPages={tickets.data.total_pages}
            onPageChange={(nextPage) => {
              const next = new URLSearchParams(searchParams);
              next.set("page", String(nextPage));
              setSearchParams(next);
            }}
          />
        </>
      )}
    </div>
  );
}
