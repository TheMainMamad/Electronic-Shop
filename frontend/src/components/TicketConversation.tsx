import { useState } from "react";
import type { ReactNode } from "react";

import type { Ticket } from "@/api/types";
import { formatJalaliDateTime } from "@/lib/persian";
import { ticketPriorityLabels, ticketStatusLabels, statusTone } from "@/lib/statusLabels";
import { Badge } from "@/components/ui/Badge";
import { Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const AUTHOR_LABELS: Record<string, string> = {
  customer: "مشتری",
  support: "پشتیبانی",
  system: "سامانه",
};

const AUTHOR_ALIGN: Record<string, string> = {
  customer: "items-start",
  support: "items-end",
  system: "items-center",
};

const AUTHOR_BUBBLE: Record<string, string> = {
  customer: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100",
  support: "bg-brand-600 text-white",
  system: "bg-amber-50 text-amber-800 text-xs dark:bg-amber-950/30 dark:text-amber-300",
};

export function TicketConversation({
  ticket,
  onReply,
  isReplying,
  disabled,
  extraHeaderActions,
}: {
  ticket: Ticket;
  onReply: (message: string) => void;
  isReplying: boolean;
  disabled?: boolean;
  extraHeaderActions?: ReactNode;
}) {
  const [message, setMessage] = useState("");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-bold">{ticket.subject}</h1>
          <p className="text-xs text-gray-400">آخرین به‌روزرسانی: {formatJalaliDateTime(ticket.updated_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={statusTone(ticket.status)}>{ticketStatusLabels[ticket.status]}</Badge>
          <Badge tone="neutral">اولویت: {ticketPriorityLabels[ticket.priority]}</Badge>
          {extraHeaderActions}
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
        {ticket.messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${AUTHOR_ALIGN[msg.author_role]}`}>
            <span className="mb-1 text-xs text-gray-400">
              {AUTHOR_LABELS[msg.author_role]} — {formatJalaliDateTime(msg.created_at)}
            </span>
            <p className={`max-w-lg whitespace-pre-line rounded-xl px-3 py-2 text-sm ${AUTHOR_BUBBLE[msg.author_role]}`}>
              {msg.body}
            </p>
          </div>
        ))}
      </div>

      {ticket.status !== "closed" && !disabled && (
        <form
          className="flex flex-col gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            if (!message.trim()) return;
            onReply(message);
            setMessage("");
          }}
        >
          <Textarea
            label="پاسخ شما"
            rows={3}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            required
          />
          <Button type="submit" loading={isReplying} className="w-fit">
            ارسال پاسخ
          </Button>
        </form>
      )}
      {ticket.status === "closed" && (
        <p className="text-sm text-gray-500">این تیکت بسته شده است و امکان ارسال پیام جدید وجود ندارد.</p>
      )}
    </div>
  );
}
