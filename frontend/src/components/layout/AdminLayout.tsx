import { NavLink, Outlet } from "react-router-dom";

import { useCurrentUser, useLogout } from "@/hooks/useAuth";
import { ThemeToggle } from "@/components/ThemeToggle";

const NAV_ITEMS = [
  { to: "/admin", label: "داشبورد", end: true },
  { to: "/admin/products", label: "محصولات" },
  { to: "/admin/categories", label: "دسته‌بندی‌ها" },
  { to: "/admin/orders", label: "سفارش‌ها" },
  { to: "/admin/users", label: "کاربران" },
  { to: "/admin/tickets", label: "تیکت‌ها" },
  { to: "/admin/reports", label: "گزارش‌ها" },
  { to: "/admin/activity", label: "گزارش فعالیت‌ها" },
];

export function AdminLayout() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950">
      <aside className="hidden w-60 shrink-0 border-l border-gray-200 bg-white p-4 md:block dark:border-gray-800 dark:bg-gray-900">
        <div className="mb-6 text-lg font-bold text-brand-700 dark:text-brand-500">پنل مدیریت</div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-900">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {user ? `خوش آمدید، ${user.first_name || user.username}` : ""}
          </span>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <button
              type="button"
              onClick={() => logout.mutate()}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
            >
              خروج
            </button>
          </div>
        </header>
        <main className="flex-1 p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
