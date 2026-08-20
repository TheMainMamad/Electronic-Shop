import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminChangeTicketStatus, adminReplyToTicket, fetchAdminTicket } from "@/api/admin";
import type { TicketStatus } from "@/api/types";
import { getErrorMessage } from "@/lib/errors";
import { ticketStatusLabels } from "@/lib/statusLabels";
import { useToastStore } from "@/stores/toastStore";
import { TicketConversation } from "@/components/TicketConversation";
import { Select } from "@/components/ui/Select";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";

export function AdminTicketDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const push = useToastStore((state) => state.push);

  const ticket = useQuery({ queryKey: ["admin", "tickets", "detail", id], queryFn: () => fetchAdminTicket(id) });

  const reply = useMutation({
    mutationFn: (message: string) => adminReplyToTicket(id, message),
    onSuccess: (data) => {
      queryClient.setQueryData(["admin", "tickets", "detail", id], data);
      push("پاسخ شما ثبت شد.", "success");
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  const changeStatus = useMutation({
    mutationFn: (status: TicketStatus) => adminChangeTicketStatus(id, status),
    onSuccess: (data) => {
      queryClient.setQueryData(["admin", "tickets", "detail", id], data);
      push("وضعیت تیکت به‌روزرسانی شد.", "success");
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  if (ticket.isLoading) return <Spinner />;
  if (ticket.isError || !ticket.data) {
    return <ErrorState message={getErrorMessage(ticket.error, "تیکت پیدا نشد.")} />;
  }

  return (
    <TicketConversation
      ticket={ticket.data}
      onReply={(message) => reply.mutate(message)}
      isReplying={reply.isPending}
      disabled={ticket.data.status === "closed"}
      extraHeaderActions={
        <Select
          value=""
          onChange={(event) => {
            if (event.target.value) changeStatus.mutate(event.target.value as TicketStatus);
          }}
          className="w-44"
        >
          <option value="">تغییر وضعیت...</option>
          {Object.entries(ticketStatusLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      }
    />
  );
}
