import { apiClient } from "@/lib/apiClient";
import type { Page, Ticket, TicketListItem, TicketPriority } from "@/api/types";

export async function fetchMyTickets(page: number, pageSize = 10): Promise<Page<TicketListItem>> {
  const { data } = await apiClient.get<Page<TicketListItem>>("/tickets", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function fetchTicket(ticketId: string): Promise<Ticket> {
  const { data } = await apiClient.get<Ticket>(`/tickets/${ticketId}`);
  return data;
}

export async function createTicket(
  subject: string,
  message: string,
  priority: TicketPriority = "normal",
): Promise<Ticket> {
  const { data } = await apiClient.post<Ticket>("/tickets", { subject, message, priority });
  return data;
}

export async function replyToTicket(ticketId: string, message: string): Promise<Ticket> {
  const { data } = await apiClient.post<Ticket>(`/tickets/${ticketId}/messages`, { message });
  return data;
}
