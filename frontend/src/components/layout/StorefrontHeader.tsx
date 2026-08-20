import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useCurrentUser, useLogout } from "@/hooks/useAuth";
import { useCart } from "@/hooks/useCart";
import { ThemeToggle } from "@/components/ThemeToggle";

export function StorefrontHeader() {
  const { data: user } = useCurrentUser();
  const { data: cart } = useCart();
  const logout = useLogout();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const cartCount = cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0;

  const handleSearchSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    navigate(`/products?search=${encodeURIComponent(search)}`);
  };

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/95 backdrop-blur dark:border-gray-800 dark:bg-gray-950/95">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
        <Link to="/" className="text-lg font-bold text-brand-700 dark:text-brand-500">
          فروشگاه الکترونیک
        </Link>

        <nav className="hidden items-center gap-4 text-sm font-medium text-gray-600 md:flex dark:text-gray-300">
          <Link to="/products" className="hover:text-brand-600">
            محصولات
          </Link>
          <Link to="/categories" className="hover:text-brand-600">
            دسته‌بندی‌ها
          </Link>
        </nav>

        <form onSubmit={handleSearchSubmit} className="order-last w-full flex-1 md:order-none md:w-auto">
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="جستجوی محصول..."
            className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900"
          />
        </form>

        <div className="flex items-center gap-3">
          <ThemeToggle />

          <Link to="/cart" className="relative rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-800" aria-label="سبد خرید">
            <CartIcon />
            {cartCount > 0 && (
              <span className="absolute -top-1 -left-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
                {cartCount > 9 ? "۹+" : cartCount}
              </span>
            )}
          </Link>

          {user ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((open) => !open)}
                className="rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                {user.first_name || user.username}
              </button>
              {menuOpen && (
                <div className="absolute left-0 top-full mt-2 w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-800 dark:bg-gray-900">
                  <MenuLink to="/dashboard" onClick={() => setMenuOpen(false)}>
                    داشبورد
                  </MenuLink>
                  <MenuLink to="/orders" onClick={() => setMenuOpen(false)}>
                    سفارش‌ها
                  </MenuLink>
                  <MenuLink to="/wallet" onClick={() => setMenuOpen(false)}>
                    کیف پول
                  </MenuLink>
                  <MenuLink to="/tickets" onClick={() => setMenuOpen(false)}>
                    تیکت‌ها
                  </MenuLink>
                  <MenuLink to="/profile" onClick={() => setMenuOpen(false)}>
                    پروفایل
                  </MenuLink>
                  {(user.role === "admin" || user.role === "super_admin" || user.role === "support") && (
                    <MenuLink to="/admin" onClick={() => setMenuOpen(false)}>
                      پنل مدیریت
                    </MenuLink>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      logout.mutate();
                    }}
                    className="block w-full px-4 py-2 text-right text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-800"
                  >
                    خروج
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              to="/login"
              className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              ورود
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

function MenuLink({ to, onClick, children }: { to: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
    >
      {children}
    </Link>
  );
}

function CartIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="9" cy="21" r="1" />
      <circle cx="19" cy="21" r="1" />
      <path d="M1 1h3l2.4 12.4a2 2 0 0 0 2 1.6h9.2a2 2 0 0 0 2-1.6L22 5H5" />
    </svg>
  );
}
