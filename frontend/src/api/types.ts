export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export type UserRole = "customer" | "support" | "admin" | "super_admin";

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
  role: UserRole;
  is_verified: boolean;
}

export interface AdminUser {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  sort_order: number;
  parent_id: string | null;
  children: Category[];
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  slug: string;
  short_description: string;
  description: string;
  price: string;
  discount_price: string | null;
  brand: string;
  category_id: string;
  images: string[];
  specifications: Record<string, string>;
  is_active: boolean;
  is_featured: boolean;
  is_popular: boolean;
  available_stock: number;
}

export interface CartItemPublic {
  product_id: string;
  name: string;
  slug: string;
  unit_price: string;
  quantity: number;
  subtotal: string;
  available_stock: number;
}

export interface CartSummary {
  items: CartItemPublic[];
  subtotal: string;
  total: string;
}

export type OrderStatus =
  | "pending"
  | "awaiting_payment"
  | "paid"
  | "processing"
  | "shipped"
  | "completed"
  | "cancelled"
  | "payment_failed"
  | "refunded";

export interface OrderItem {
  product_id: string | null;
  product_name: string;
  sku: string;
  unit_price: string;
  quantity: number;
  subtotal: string;
}

export interface ShippingAddress {
  recipient_name: string;
  province: string;
  city: string;
  address_line: string;
  postal_code: string;
  phone_number: string;
}

export interface Order {
  id: string;
  status: OrderStatus;
  subtotal: string;
  total: string;
  shipping_address: ShippingAddress | null;
  items: OrderItem[];
  created_at: string;
}

export type PaymentStatus = "initiated" | "pending" | "verified" | "failed";

export interface WalletTransaction {
  id: string;
  type: "deposit" | "purchase" | "refund" | "admin_credit" | "admin_debit";
  amount: string;
  balance_after: string;
  note: string | null;
  created_at: string;
}

export interface Wallet {
  id: string;
  balance: string;
}

export type TicketStatus = "open" | "waiting_for_support" | "waiting_for_customer" | "closed";
export type TicketPriority = "low" | "normal" | "high" | "urgent";

export interface TicketMessage {
  id: string;
  author_id: string | null;
  author_role: "customer" | "support" | "system";
  body: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  user_id: string;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  last_response_at: string;
  messages: TicketMessage[];
}

export interface TicketListItem {
  id: string;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  last_response_at: string;
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  new_users_today: number;
  total_products: number;
  low_stock_products: number;
  out_of_stock_products: number;
  total_orders: number;
  orders_today: number;
  pending_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  successful_payments: number;
  failed_payments: number;
  total_sales: string;
  wallet_transactions: number;
  open_tickets: number;
  unanswered_tickets: number;
  closed_tickets: number;
  active_carts: number;
  abandoned_carts: number;
}

export interface DailyPoint {
  date: string;
  value: number;
}

export interface RevenuePoint {
  date: string;
  value: string;
}

export interface DistributionSlice {
  label: string;
  count: number;
}

export interface DashboardCharts {
  orders_per_day: DailyPoint[];
  revenue_per_day: RevenuePoint[];
  registrations_per_day: DailyPoint[];
  order_status_distribution: DistributionSlice[];
  payment_status_distribution: DistributionSlice[];
  products_by_category: DistributionSlice[];
  ticket_status_distribution: DistributionSlice[];
}

export interface AdminReport {
  range: string;
  start_date: string;
  end_date: string;
  sales: { order_count: number; total_revenue: string; average_order_value: string };
  orders: { by_status: DistributionSlice[] };
  users: { new_registrations: number };
  products: { total_active_products: number; low_stock_count: number; out_of_stock_count: number };
  payments: { verified_count: number; verified_amount: string; failed_count: number };
  tickets: { by_status: DistributionSlice[]; auto_closed_count: number };
  category_performance: { category_name: string; order_item_count: number; revenue: string }[];
}

export interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  audit_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown;
    request_id: string | null;
  };
}
