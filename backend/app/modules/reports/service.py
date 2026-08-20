import datetime as dt
from datetime import UTC
from decimal import Decimal

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.cart.models import Cart, CartItem
from app.modules.catalog.models import Category, Product, ProductInventory
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.reports.schemas import (
    AdminReport,
    CategoryPerformanceItem,
    DailyPoint,
    DashboardCharts,
    DashboardStats,
    DistributionSlice,
    OrdersReport,
    PaymentsReport,
    ProductsReport,
    RecentActivityItem,
    ReportRange,
    RevenuePoint,
    SalesReport,
    TicketsReport,
    UsersReport,
)
from app.modules.tickets.models import Ticket, TicketStatus
from app.modules.users.models import User
from app.modules.wallet.models import WalletTransaction

_ABANDONED_CART_AGE = dt.timedelta(hours=24)
_COMPLETED_ORDER_STATUSES = (
    OrderStatus.paid,
    OrderStatus.processing,
    OrderStatus.shipped,
    OrderStatus.completed,
)
_PENDING_ORDER_STATUSES = (OrderStatus.pending, OrderStatus.awaiting_payment)


def resolve_range(
    range_: ReportRange, start_date: dt.date | None, end_date: dt.date | None
) -> tuple[dt.datetime, dt.datetime]:
    now = dt.datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if range_ == "today":
        return today_start, now
    if range_ == "7d":
        return today_start - dt.timedelta(days=6), now
    if range_ == "30d":
        return today_start - dt.timedelta(days=29), now

    if start_date is None or end_date is None:
        raise ValueError("برای بازه سفارشی، تاریخ شروع و پایان الزامی است.")
    start = dt.datetime.combine(start_date, dt.time.min, tzinfo=UTC)
    end = dt.datetime.combine(end_date, dt.time.max, tzinfo=UTC)
    return start, end


async def get_dashboard_stats(session: AsyncSession) -> DashboardStats:
    now = dt.datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    active_users = (
        await session.execute(
            select(func.count()).select_from(User).where(User.is_active.is_(True))
        )
    ).scalar_one()
    new_users_today = (
        await session.execute(
            select(func.count()).select_from(User).where(User.created_at >= today_start)
        )
    ).scalar_one()

    total_products = (
        await session.execute(select(func.count()).select_from(Product))
    ).scalar_one()
    low_stock_products = (
        await session.execute(
            select(func.count())
            .select_from(ProductInventory)
            .where(
                ProductInventory.stock_total - ProductInventory.stock_reserved > 0,
                ProductInventory.stock_total - ProductInventory.stock_reserved <= 5,
            )
        )
    ).scalar_one()
    out_of_stock_products = (
        await session.execute(
            select(func.count())
            .select_from(ProductInventory)
            .where(ProductInventory.stock_total - ProductInventory.stock_reserved <= 0)
        )
    ).scalar_one()

    total_orders = (await session.execute(select(func.count()).select_from(Order))).scalar_one()
    orders_today = (
        await session.execute(
            select(func.count()).select_from(Order).where(Order.created_at >= today_start)
        )
    ).scalar_one()
    pending_orders = (
        await session.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.status.in_(_PENDING_ORDER_STATUSES))
        )
    ).scalar_one()
    completed_orders = (
        await session.execute(
            select(func.count()).select_from(Order).where(Order.status == OrderStatus.completed)
        )
    ).scalar_one()
    cancelled_orders = (
        await session.execute(
            select(func.count()).select_from(Order).where(Order.status == OrderStatus.cancelled)
        )
    ).scalar_one()

    successful_payments = (
        await session.execute(
            select(func.count())
            .select_from(Payment)
            .where(Payment.status == PaymentStatus.verified)
        )
    ).scalar_one()
    failed_payments = (
        await session.execute(
            select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.failed)
        )
    ).scalar_one()

    total_sales = (
        await session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.status.in_(_COMPLETED_ORDER_STATUSES)
            )
        )
    ).scalar_one()

    wallet_transactions = (
        await session.execute(select(func.count()).select_from(WalletTransaction))
    ).scalar_one()

    open_tickets = (
        await session.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status != TicketStatus.closed)
        )
    ).scalar_one()
    unanswered_tickets = (
        await session.execute(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == TicketStatus.waiting_for_support)
        )
    ).scalar_one()
    closed_tickets = (
        await session.execute(
            select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.closed)
        )
    ).scalar_one()

    active_carts = (
        await session.execute(
            select(func.count(func.distinct(CartItem.cart_id))).select_from(CartItem)
        )
    ).scalar_one()
    abandoned_cutoff = now - _ABANDONED_CART_AGE
    abandoned_carts = (
        await session.execute(
            select(func.count(func.distinct(Cart.id)))
            .select_from(Cart)
            .join(CartItem, CartItem.cart_id == Cart.id)
            .where(Cart.updated_at < abandoned_cutoff)
        )
    ).scalar_one()

    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        new_users_today=new_users_today,
        total_products=total_products,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        total_orders=total_orders,
        orders_today=orders_today,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        total_sales=total_sales,
        wallet_transactions=wallet_transactions,
        open_tickets=open_tickets,
        unanswered_tickets=unanswered_tickets,
        closed_tickets=closed_tickets,
        active_carts=active_carts,
        abandoned_carts=abandoned_carts,
    )


async def get_recent_activity(
    session: AsyncSession, *, limit: int = 20
) -> list[RecentActivityItem]:
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    return [
        RecentActivityItem(
            action=row.action, resource_type=row.resource_type, created_at=row.created_at
        )
        for row in result.scalars()
    ]


def _fill_daily_series(
    raw: dict[dt.date, int], *, days: int, today: dt.date
) -> list[DailyPoint]:
    start = today - dt.timedelta(days=days - 1)
    return [
        DailyPoint(
            date=start + dt.timedelta(days=i),
            value=raw.get(start + dt.timedelta(days=i), 0),
        )
        for i in range(days)
    ]


async def get_dashboard_charts(session: AsyncSession, *, days: int = 14) -> DashboardCharts:
    now = dt.datetime.now(UTC)
    today = now.date()
    window_start = dt.datetime.combine(today - dt.timedelta(days=days - 1), dt.time.min, tzinfo=UTC)

    orders_rows = (
        await session.execute(
            select(cast(Order.created_at, Date), func.count())
            .where(Order.created_at >= window_start)
            .group_by(cast(Order.created_at, Date))
        )
    ).all()
    orders_per_day = _fill_daily_series(
        {row[0]: row[1] for row in orders_rows}, days=days, today=today
    )

    revenue_rows = (
        await session.execute(
            select(cast(Order.created_at, Date), func.coalesce(func.sum(Order.total), 0))
            .where(Order.created_at >= window_start, Order.status.in_(_COMPLETED_ORDER_STATUSES))
            .group_by(cast(Order.created_at, Date))
        )
    ).all()
    revenue_map: dict[dt.date, Decimal] = {row[0]: row[1] for row in revenue_rows}
    start = today - dt.timedelta(days=days - 1)
    revenue_per_day = [
        RevenuePoint(
            date=start + dt.timedelta(days=i),
            value=revenue_map.get(start + dt.timedelta(days=i), Decimal(0)),
        )
        for i in range(days)
    ]

    registration_rows = (
        await session.execute(
            select(cast(User.created_at, Date), func.count())
            .where(User.created_at >= window_start)
            .group_by(cast(User.created_at, Date))
        )
    ).all()
    registrations_per_day = _fill_daily_series(
        {row[0]: row[1] for row in registration_rows}, days=days, today=today
    )

    order_status_rows = (
        await session.execute(select(Order.status, func.count()).group_by(Order.status))
    ).all()
    order_status_distribution = [
        DistributionSlice(label=row[0].value, count=row[1]) for row in order_status_rows
    ]

    payment_status_rows = (
        await session.execute(select(Payment.status, func.count()).group_by(Payment.status))
    ).all()
    payment_status_distribution = [
        DistributionSlice(label=row[0].value, count=row[1]) for row in payment_status_rows
    ]

    products_by_category_rows = (
        await session.execute(
            select(Category.name, func.count(Product.id))
            .join(Product, Product.category_id == Category.id)
            .group_by(Category.name)
        )
    ).all()
    products_by_category = [
        DistributionSlice(label=row[0], count=row[1]) for row in products_by_category_rows
    ]

    ticket_status_rows = (
        await session.execute(select(Ticket.status, func.count()).group_by(Ticket.status))
    ).all()
    ticket_status_distribution = [
        DistributionSlice(label=row[0].value, count=row[1]) for row in ticket_status_rows
    ]

    return DashboardCharts(
        orders_per_day=orders_per_day,
        revenue_per_day=revenue_per_day,
        registrations_per_day=registrations_per_day,
        order_status_distribution=order_status_distribution,
        payment_status_distribution=payment_status_distribution,
        products_by_category=products_by_category,
        ticket_status_distribution=ticket_status_distribution,
    )


async def get_admin_report(
    session: AsyncSession,
    *,
    range_: ReportRange,
    start_date: dt.date | None,
    end_date: dt.date | None,
) -> AdminReport:
    start, end = resolve_range(range_, start_date, end_date)

    order_count = (
        await session.execute(
            select(func.count())
            .select_from(Order)
            .where(
                Order.created_at.between(start, end),
                Order.status.in_(_COMPLETED_ORDER_STATUSES),
            )
        )
    ).scalar_one()
    total_revenue = (
        await session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.created_at.between(start, end), Order.status.in_(_COMPLETED_ORDER_STATUSES)
            )
        )
    ).scalar_one()
    average_order_value = (total_revenue / order_count) if order_count else Decimal(0)

    orders_by_status_rows = (
        await session.execute(
            select(Order.status, func.count())
            .where(Order.created_at.between(start, end))
            .group_by(Order.status)
        )
    ).all()

    new_registrations = (
        await session.execute(
            select(func.count()).select_from(User).where(User.created_at.between(start, end))
        )
    ).scalar_one()

    total_active_products = (
        await session.execute(
            select(func.count()).select_from(Product).where(Product.is_active.is_(True))
        )
    ).scalar_one()
    low_stock_count = (
        await session.execute(
            select(func.count())
            .select_from(ProductInventory)
            .where(
                ProductInventory.stock_total - ProductInventory.stock_reserved > 0,
                ProductInventory.stock_total - ProductInventory.stock_reserved <= 5,
            )
        )
    ).scalar_one()
    out_of_stock_count = (
        await session.execute(
            select(func.count())
            .select_from(ProductInventory)
            .where(ProductInventory.stock_total - ProductInventory.stock_reserved <= 0)
        )
    ).scalar_one()

    verified_count = (
        await session.execute(
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.verified_at.between(start, end), Payment.status == PaymentStatus.verified
            )
        )
    ).scalar_one()
    verified_amount = (
        await session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.verified_at.between(start, end), Payment.status == PaymentStatus.verified
            )
        )
    ).scalar_one()
    failed_count = (
        await session.execute(
            select(func.count())
            .select_from(Payment)
            .where(Payment.created_at.between(start, end), Payment.status == PaymentStatus.failed)
        )
    ).scalar_one()

    tickets_by_status_rows = (
        await session.execute(
            select(Ticket.status, func.count())
            .where(Ticket.created_at.between(start, end))
            .group_by(Ticket.status)
        )
    ).all()
    auto_closed_count = (
        await session.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.action == "ticket.auto_closed",
                AuditLog.created_at.between(start, end),
            )
        )
    ).scalar_one()

    category_rows = (
        await session.execute(
            select(
                Category.name,
                func.count(OrderItem.id),
                func.coalesce(func.sum(OrderItem.subtotal), 0),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .join(Category, Category.id == Product.category_id)
            .where(
                Order.created_at.between(start, end), Order.status.in_(_COMPLETED_ORDER_STATUSES)
            )
            .group_by(Category.name)
        )
    ).all()

    return AdminReport(
        range=range_,
        start_date=start,
        end_date=end,
        sales=SalesReport(
            order_count=order_count,
            total_revenue=total_revenue,
            average_order_value=average_order_value,
        ),
        orders=OrdersReport(
            by_status=[
                DistributionSlice(label=row[0].value, count=row[1])
                for row in orders_by_status_rows
            ]
        ),
        users=UsersReport(new_registrations=new_registrations),
        products=ProductsReport(
            total_active_products=total_active_products,
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
        ),
        payments=PaymentsReport(
            verified_count=verified_count,
            verified_amount=verified_amount,
            failed_count=failed_count,
        ),
        tickets=TicketsReport(
            by_status=[
                DistributionSlice(label=row[0].value, count=row[1])
                for row in tickets_by_status_rows
            ],
            auto_closed_count=auto_closed_count,
        ),
        category_performance=[
            CategoryPerformanceItem(category_name=row[0], order_item_count=row[1], revenue=row[2])
            for row in category_rows
        ],
    )
