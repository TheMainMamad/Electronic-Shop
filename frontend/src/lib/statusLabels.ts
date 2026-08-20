export const orderStatusLabels: Record<string, string> = {
  pending: "در انتظار",
  awaiting_payment: "در انتظار پرداخت",
  paid: "پرداخت‌شده",
  processing: "در حال پردازش",
  shipped: "ارسال‌شده",
  completed: "تکمیل‌شده",
  cancelled: "لغوشده",
  payment_failed: "پرداخت ناموفق",
  refunded: "بازپرداخت‌شده",
};

export const paymentStatusLabels: Record<string, string> = {
  initiated: "شروع‌شده",
  pending: "در حال بررسی",
  verified: "تأییدشده",
  failed: "ناموفق",
};

export const ticketStatusLabels: Record<string, string> = {
  open: "باز",
  waiting_for_support: "در انتظار پاسخ پشتیبانی",
  waiting_for_customer: "در انتظار پاسخ شما",
  closed: "بسته‌شده",
};

export const ticketPriorityLabels: Record<string, string> = {
  low: "کم",
  normal: "عادی",
  high: "بالا",
  urgent: "فوری",
};

export const walletTransactionTypeLabels: Record<string, string> = {
  deposit: "افزایش موجودی",
  purchase: "خرید",
  refund: "بازپرداخت",
  admin_credit: "افزایش توسط مدیر",
  admin_debit: "کاهش توسط مدیر",
};

export const userRoleLabels: Record<string, string> = {
  customer: "مشتری",
  support: "پشتیبانی",
  admin: "مدیر",
  super_admin: "مدیر ارشد",
};

const STATUS_BADGE_TONES: Record<string, "success" | "warning" | "danger" | "neutral" | "info"> = {
  paid: "success",
  verified: "success",
  completed: "success",
  closed: "neutral",
  cancelled: "danger",
  payment_failed: "danger",
  failed: "danger",
  refunded: "info",
  awaiting_payment: "warning",
  pending: "warning",
  processing: "info",
  shipped: "info",
  waiting_for_support: "warning",
  waiting_for_customer: "warning",
  open: "info",
  initiated: "neutral",
};

export function statusTone(status: string): "success" | "warning" | "danger" | "neutral" | "info" {
  return STATUS_BADGE_TONES[status] ?? "neutral";
}
