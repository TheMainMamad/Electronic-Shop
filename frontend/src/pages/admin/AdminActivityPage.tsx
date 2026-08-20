import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchAuditLogs } from "@/api/admin";
import { formatJalaliDateTime } from "@/lib/persian";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function AdminActivityPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");

  const logs = useQuery({
    queryKey: ["admin", "audit-logs", page],
    queryFn: () => fetchAuditLogs(page, 20),
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-bold">گزارش فعالیت‌ها</h1>

      {logs.isLoading && <Spinner />}
      {logs.data && logs.data.items.length === 0 && <EmptyState title="فعالیتی ثبت نشده است." />}
      {logs.data && logs.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                <tr>
                  <th className="px-3 py-2 text-right">عملیات</th>
                  <th className="px-3 py-2 text-right">نوع منبع</th>
                  <th className="px-3 py-2 text-right">شناسه منبع</th>
                  <th className="px-3 py-2 text-right">زمان</th>
                </tr>
              </thead>
              <tbody>
                {logs.data.items.map((log) => (
                  <tr key={log.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="ltr-inline px-3 py-2 text-xs">{log.action}</td>
                    <td className="px-3 py-2">{log.resource_type}</td>
                    <td className="ltr-inline px-3 py-2 text-xs text-gray-500">
                      {log.resource_id ? log.resource_id.slice(0, 8) : "—"}
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500">{formatJalaliDateTime(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={logs.data.page}
            totalPages={logs.data.total_pages}
            onPageChange={(nextPage) => setSearchParams({ page: String(nextPage) })}
          />
        </>
      )}

      <Card>
        <h2 className="mb-2 font-bold">اطلاعات سیستم</h2>
        <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
          <dt className="text-gray-500">نسخه برنامه</dt>
          <dd className="ltr-inline">v1.0.0</dd>
          <dt className="text-gray-500">محیط اجرا</dt>
          <dd>تولید</dd>
        </dl>
      </Card>
    </div>
  );
}
