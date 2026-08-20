import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createTicket, fetchMyTickets } from "@/api/tickets";
import type { TicketPriority } from "@/api/types";
import { formatJalaliDateTime } from "@/lib/persian";
import { getErrorMessage } from "@/lib/errors";
import { ticketPriorityLabels, ticketStatusLabels, statusTone } from "@/lib/statusLabels";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function TicketsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");
  const [showForm, setShowForm] = useState(false);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [priority, setPriority] = useState<TicketPriority>("normal");
  const push = useToastStore((state) => state.push);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const tickets = useQuery({
    queryKey: ["tickets", "list", page],
    queryFn: () => fetchMyTickets(page, 10),
  });

  const create = useMutation({
    mutationFn: () => createTicket(subject, message, priority),
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      navigate(`/tickets/${ticket.id}`);
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">تیکت‌های پشتیبانی</h1>
        <Button onClick={() => setShowForm((v) => !v)}>{showForm ? "انصراف" : "تیکت جدید"}</Button>
      </div>

      {showForm && (
        <Card>
          <form
            className="flex flex-col gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              create.mutate();
            }}
          >
            <Input label="موضوع" required value={subject} onChange={(e) => setSubject(e.target.value)} />
            <Select label="اولویت" value={priority} onChange={(e) => setPriority(e.target.value as TicketPriority)}>
              {Object.entries(ticketPriorityLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
            <Textarea
              label="پیام"
              required
              rows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <Button type="submit" loading={create.isPending} className="w-fit">
              ثبت تیکت
            </Button>
          </form>
        </Card>
      )}

      {tickets.isLoading && <Spinner />}
      {tickets.data && tickets.data.items.length === 0 && (
        <EmptyState title="تیکت جدیدی ندارید." />
      )}
      {tickets.data && tickets.data.items.length > 0 && (
        <>
          <div className="flex flex-col gap-2">
            {tickets.data.items.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/tickets/${ticket.id}`}
                className="flex items-center justify-between rounded-xl border border-gray-200 p-3 hover:border-brand-500 dark:border-gray-800"
              >
                <div>
                  <p className="font-medium">{ticket.subject}</p>
                  <p className="text-xs text-gray-400">{formatJalaliDateTime(ticket.last_response_at)}</p>
                </div>
                <Badge tone={statusTone(ticket.status)}>{ticketStatusLabels[ticket.status]}</Badge>
              </Link>
            ))}
          </div>
          <Pagination
            page={tickets.data.page}
            totalPages={tickets.data.total_pages}
            onPageChange={(nextPage) => setSearchParams({ page: String(nextPage) })}
          />
        </>
      )}
    </div>
  );
}
