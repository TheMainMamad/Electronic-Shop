import { apiClient } from "@/lib/apiClient";
import { newIdempotencyKey } from "@/lib/idempotency";
import type {
  AdminReport,
  AdminUser,
  AuditLogEntry,
  Category,
  DashboardCharts,
  DashboardStats,
  Order,
  OrderStatus,
  Page,
  Product,
  Ticket,
  TicketListItem,
  TicketStatus,
  Wallet,
  WalletTransaction,
} from "@/api/types";

// --- Dashboard & reports ---

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/admin/dashboard/stats");
  return data;
}

export async function fetchDashboardCharts(days = 14): Promise<DashboardCharts> {
  const { data } = await apiClient.get<DashboardCharts>("/admin/dashboard/charts", {
    params: { days },
  });
  return data;
}

export async function fetchAdminReport(
  range: "today" | "7d" | "30d" | "custom",
  startDate?: string,
  endDate?: string,
): Promise<AdminReport> {
  const { data } = await apiClient.get<AdminReport>("/admin/reports", {
    params: { range, start_date: startDate, end_date: endDate },
  });
  return data;
}

export async function fetchAuditLogs(page: number, pageSize = 20): Promise<Page<AuditLogEntry>> {
  const { data } = await apiClient.get<Page<AuditLogEntry>>("/admin/audit-logs", {
    params: { page, page_size: pageSize },
  });
  return data;
}

// --- Categories ---

export async function createCategory(payload: {
  name: string;
  slug: string;
  parent_id?: string | null;
}): Promise<Category> {
  const { data } = await apiClient.post<Category>("/admin/categories", payload);
  return data;
}

export async function updateCategory(
  categoryId: string,
  payload: { name?: string; is_active?: boolean; sort_order?: number },
): Promise<Category> {
  const { data } = await apiClient.patch<Category>(`/admin/categories/${categoryId}`, payload);
  return data;
}

export async function moveCategory(categoryId: string, newParentId: string | null): Promise<Category> {
  const { data } = await apiClient.post<Category>(`/admin/categories/${categoryId}/move`, {
    new_parent_id: newParentId,
  });
  return data;
}

export async function deleteCategory(categoryId: string): Promise<void> {
  await apiClient.delete(`/admin/categories/${categoryId}`);
}

// --- Products ---

export interface AdminProductPayload {
  sku: string;
  name: string;
  slug: string;
  short_description?: string;
  description?: string;
  price: string;
  discount_price?: string | null;
  brand?: string;
  category_id: string;
  images?: string[];
  specifications?: Record<string, string>;
  is_active?: boolean;
  is_featured?: boolean;
  is_popular?: boolean;
  initial_stock?: number;
}

export async function createProduct(payload: AdminProductPayload): Promise<Product> {
  const { data } = await apiClient.post<Product>("/admin/products", payload);
  return data;
}

export async function updateProduct(
  productId: string,
  payload: Partial<AdminProductPayload>,
): Promise<Product> {
  const { data } = await apiClient.patch<Product>(`/admin/products/${productId}`, payload);
  return data;
}

export async function archiveProduct(productId: string): Promise<void> {
  await apiClient.delete(`/admin/products/${productId}`);
}

export async function restockProduct(productId: string, delta: number, reason: string): Promise<void> {
  await apiClient.post(`/admin/products/${productId}/inventory/restock`, { delta, reason });
}

export async function adjustProductInventory(
  productId: string,
  delta: number,
  reason: string,
): Promise<void> {
  await apiClient.post(`/admin/products/${productId}/inventory/adjust`, { delta, reason });
}

export async function uploadProductImage(file: File): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<{ url: string }>("/admin/uploads/product-image", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// --- Orders ---

export async function fetchAdminOrders(page: number, pageSize = 20): Promise<Page<Order>> {
  const { data } = await apiClient.get<Page<Order>>("/admin/orders", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function updateOrderStatus(
  orderId: string,
  newStatus: OrderStatus,
  note?: string,
): Promise<Order> {
  const { data } = await apiClient.patch<Order>(`/admin/orders/${orderId}/status`, {
    new_status: newStatus,
    note,
  });
  return data;
}

// --- Users ---

export async function fetchAdminUsers(
  page: number,
  pageSize = 20,
  search?: string,
): Promise<Page<AdminUser>> {
  const { data } = await apiClient.get<Page<AdminUser>>("/admin/users", {
    params: { page, page_size: pageSize, search },
  });
  return data;
}

export async function fetchAdminUser(userId: string): Promise<AdminUser> {
  const { data } = await apiClient.get<AdminUser>(`/admin/users/${userId}`);
  return data;
}

export async function updateAdminUser(
  userId: string,
  payload: { role?: string; is_active?: boolean },
): Promise<AdminUser> {
  const { data } = await apiClient.patch<AdminUser>(`/admin/users/${userId}`, payload);
  return data;
}

// --- Tickets ---

export async function fetchAdminTickets(
  page: number,
  pageSize = 20,
  status?: TicketStatus,
): Promise<Page<TicketListItem>> {
  const { data } = await apiClient.get<Page<TicketListItem>>("/admin/tickets", {
    params: { page, page_size: pageSize, ticket_status: status },
  });
  return data;
}

export async function fetchAdminTicket(ticketId: string): Promise<Ticket> {
  const { data } = await apiClient.get<Ticket>(`/admin/tickets/${ticketId}`);
  return data;
}

export async function adminReplyToTicket(ticketId: string, message: string): Promise<Ticket> {
  const { data } = await apiClient.post<Ticket>(`/admin/tickets/${ticketId}/messages`, { message });
  return data;
}

export async function adminChangeTicketStatus(ticketId: string, status: TicketStatus): Promise<Ticket> {
  const { data } = await apiClient.patch<Ticket>(`/admin/tickets/${ticketId}/status`, { status });
  return data;
}

// --- Wallet ---

export async function fetchAdminWallet(userId: string): Promise<Wallet> {
  const { data } = await apiClient.get<Wallet>(`/admin/wallets/${userId}`);
  return data;
}

export async function adminCreditWallet(
  userId: string,
  amount: string,
  reason: string,
): Promise<WalletTransaction> {
  const { data } = await apiClient.post<WalletTransaction>(
    `/admin/wallets/${userId}/credit`,
    { amount, reason },
    { headers: { "Idempotency-Key": newIdempotencyKey() } },
  );
  return data;
}

export async function adminDebitWallet(
  userId: string,
  amount: string,
  reason: string,
): Promise<WalletTransaction> {
  const { data } = await apiClient.post<WalletTransaction>(
    `/admin/wallets/${userId}/debit`,
    { amount, reason },
    { headers: { "Idempotency-Key": newIdempotencyKey() } },
  );
  return data;
}
