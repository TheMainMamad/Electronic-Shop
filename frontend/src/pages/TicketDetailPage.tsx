import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchTicket, replyToTicket } from "@/api/tickets";
import { getErrorMessage } from "@/lib/errors";
import { useToastStore } from "@/stores/toastStore";
import { TicketConversation } from "@/components/TicketConversation";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";

export function TicketDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const push = useToastStore((state) => state.push);

  const ticket = useQuery({ queryKey: ["tickets", "detail", id], queryFn: () => fetchTicket(id) });

  const reply = useMutation({
    mutationFn: (message: string) => replyToTicket(id, message),
    onSuccess: (data) => {
      queryClient.setQueryData(["tickets", "detail", id], data);
      push("پیام شما ثبت شد.", "success");
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
    />
  );
}
