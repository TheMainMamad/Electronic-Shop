import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchAdminUsers } from "@/api/admin";
import { formatJalaliDate } from "@/lib/persian";
import { userRoleLabels } from "@/lib/statusLabels";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export function AdminUsersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get("page") ?? "1");
  const [search, setSearch] = useState(searchParams.get("search") ?? "");

  const users = useQuery({
    queryKey: ["admin", "users", page, searchParams.get("search")],
    queryFn: () => fetchAdminUsers(page, 20, searchParams.get("search") || undefined),
  });

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-bold">کاربران</h1>

      <form
        className="flex max-w-sm gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setSearchParams({ page: "1", search });
        }}
      >
        <Input placeholder="جستجو بر اساس ایمیل یا نام کاربری..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <Button type="submit" variant="secondary">
          جستجو
        </Button>
      </form>

      {users.isLoading && <Spinner />}
      {users.data && users.data.items.length === 0 && <EmptyState title="کاربری پیدا نشد." />}
      {users.data && users.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                <tr>
                  <th className="px-3 py-2 text-right">نام کاربری</th>
                  <th className="px-3 py-2 text-right">ایمیل</th>
                  <th className="px-3 py-2 text-right">نقش</th>
                  <th className="px-3 py-2 text-right">وضعیت</th>
                  <th className="px-3 py-2 text-right">تاریخ عضویت</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {users.data.items.map((user) => (
                  <tr key={user.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="ltr-inline px-3 py-2">{user.username}</td>
                    <td className="ltr-inline px-3 py-2 text-xs text-gray-500">{user.email}</td>
                    <td className="px-3 py-2">{userRoleLabels[user.role]}</td>
                    <td className="px-3 py-2">
                      <Badge tone={user.is_active ? "success" : "danger"}>
                        {user.is_active ? "فعال" : "غیرفعال"}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500">{formatJalaliDate(user.created_at)}</td>
                    <td className="px-3 py-2">
                      <Link to={`/admin/users/${user.id}`} className="text-brand-600 hover:underline">
                        جزئیات
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={users.data.page}
            totalPages={users.data.total_pages}
            onPageChange={(nextPage) => setSearchParams({ page: String(nextPage), search })}
          />
        </>
      )}
    </div>
  );
}
