import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.common.money import Money

ReportRange = Literal["today", "7d", "30d", "custom"]


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    total_products: int
    low_stock_products: int
    out_of_stock_products: int
    total_orders: int
    orders_today: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    successful_payments: int
    failed_payments: int
    total_sales: Money
    wallet_transactions: int
    open_tickets: int
    unanswered_tickets: int
    closed_tickets: int
    active_carts: int
    abandoned_carts: int


class RecentActivityItem(BaseModel):
    action: str
    resource_type: str
    created_at: dt.datetime


class DailyPoint(BaseModel):
    date: dt.date
    value: int


class RevenuePoint(BaseModel):
    date: dt.date
    value: Money


class DistributionSlice(BaseModel):
    label: str
    count: int


class DashboardCharts(BaseModel):
    orders_per_day: list[DailyPoint]
    revenue_per_day: list[RevenuePoint]
    registrations_per_day: list[DailyPoint]
    order_status_distribution: list[DistributionSlice]
    payment_status_distribution: list[DistributionSlice]
    products_by_category: list[DistributionSlice]
    ticket_status_distribution: list[DistributionSlice]


class SalesReport(BaseModel):
    order_count: int
    total_revenue: Money
    average_order_value: Money


class OrdersReport(BaseModel):
    by_status: list[DistributionSlice]


class UsersReport(BaseModel):
    new_registrations: int


class ProductsReport(BaseModel):
    total_active_products: int
    low_stock_count: int
    out_of_stock_count: int


class PaymentsReport(BaseModel):
    verified_count: int
    verified_amount: Money
    failed_count: int


class TicketsReport(BaseModel):
    by_status: list[DistributionSlice]
    auto_closed_count: int


class CategoryPerformanceItem(BaseModel):
    category_name: str
    order_item_count: int
    revenue: Money


class AdminReport(BaseModel):
    range: ReportRange
    start_date: dt.datetime
    end_date: dt.datetime
    sales: SalesReport
    orders: OrdersReport
    users: UsersReport
    products: ProductsReport
    payments: PaymentsReport
    tickets: TicketsReport
    category_performance: list[CategoryPerformanceItem]
