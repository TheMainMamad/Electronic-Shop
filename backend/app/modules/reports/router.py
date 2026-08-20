import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.db.session import get_db_session
from app.modules.auth.dependencies import require_permission
from app.modules.reports.schemas import AdminReport, DashboardCharts, DashboardStats, ReportRange
from app.modules.reports.service import get_admin_report, get_dashboard_charts, get_dashboard_stats

router = APIRouter(prefix="/admin/dashboard", tags=["reports"])
reports_router = APIRouter(prefix="/admin/reports", tags=["reports"])


@router.get(
    "/stats",
    response_model=DashboardStats,
    dependencies=[Depends(require_permission("report.read"))],
)
async def dashboard_stats(session: AsyncSession = Depends(get_db_session)) -> DashboardStats:
    return await get_dashboard_stats(session)


@router.get(
    "/charts",
    response_model=DashboardCharts,
    dependencies=[Depends(require_permission("report.read"))],
)
async def dashboard_charts(
    session: AsyncSession = Depends(get_db_session),
    days: int = Query(default=14, ge=7, le=90),
) -> DashboardCharts:
    return await get_dashboard_charts(session, days=days)


@reports_router.get(
    "",
    response_model=AdminReport,
    dependencies=[Depends(require_permission("report.read"))],
)
async def admin_report(
    session: AsyncSession = Depends(get_db_session),
    range: ReportRange = "7d",  # noqa: A002 - matches the query param name
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
) -> AdminReport:
    try:
        return await get_admin_report(
            session, range_=range, start_date=start_date, end_date=end_date
        )
    except ValueError as exc:
        raise AppError(str(exc)) from exc
