import { lazy } from "react";
import { createBrowserRouter } from "react-router-dom";

import { StorefrontLayout } from "@/components/layout/StorefrontLayout";
import { AdminSuspense } from "@/components/AdminSuspense";
import { RequireAdmin } from "@/components/RequireAdmin";
import { RequireAuth } from "@/components/RequireAuth";

import { HomePage } from "@/pages/HomePage";
import { ProductsPage } from "@/pages/ProductsPage";
import { ProductDetailPage } from "@/pages/ProductDetailPage";
import { CategoriesPage } from "@/pages/CategoriesPage";
import { CartPage } from "@/pages/CartPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { CheckoutPage } from "@/pages/CheckoutPage";
import { PaymentResultPage } from "@/pages/PaymentResultPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { OrdersPage } from "@/pages/OrdersPage";
import { OrderDetailPage } from "@/pages/OrderDetailPage";
import { WalletPage } from "@/pages/WalletPage";
import { TicketsPage } from "@/pages/TicketsPage";
import { TicketDetailPage } from "@/pages/TicketDetailPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { ForbiddenPage } from "@/pages/ForbiddenPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

// The admin panel (and recharts, its heaviest dependency) is only ever
// needed by admin/support users, so it's kept out of the storefront's
// initial bundle entirely.
const AdminLayout = lazy(() =>
  import("@/components/layout/AdminLayout").then((m) => ({ default: m.AdminLayout })),
);
const AdminDashboardPage = lazy(() =>
  import("@/pages/admin/AdminDashboardPage").then((m) => ({ default: m.AdminDashboardPage })),
);
const AdminProductsPage = lazy(() =>
  import("@/pages/admin/AdminProductsPage").then((m) => ({ default: m.AdminProductsPage })),
);
const AdminProductFormPage = lazy(() =>
  import("@/pages/admin/AdminProductFormPage").then((m) => ({ default: m.AdminProductFormPage })),
);
const AdminCategoriesPage = lazy(() =>
  import("@/pages/admin/AdminCategoriesPage").then((m) => ({ default: m.AdminCategoriesPage })),
);
const AdminUsersPage = lazy(() =>
  import("@/pages/admin/AdminUsersPage").then((m) => ({ default: m.AdminUsersPage })),
);
const AdminUserDetailPage = lazy(() =>
  import("@/pages/admin/AdminUserDetailPage").then((m) => ({ default: m.AdminUserDetailPage })),
);
const AdminOrdersPage = lazy(() =>
  import("@/pages/admin/AdminOrdersPage").then((m) => ({ default: m.AdminOrdersPage })),
);
const AdminOrderDetailPage = lazy(() =>
  import("@/pages/admin/AdminOrderDetailPage").then((m) => ({ default: m.AdminOrderDetailPage })),
);
const AdminTicketsPage = lazy(() =>
  import("@/pages/admin/AdminTicketsPage").then((m) => ({ default: m.AdminTicketsPage })),
);
const AdminTicketDetailPage = lazy(() =>
  import("@/pages/admin/AdminTicketDetailPage").then((m) => ({ default: m.AdminTicketDetailPage })),
);
const AdminReportsPage = lazy(() =>
  import("@/pages/admin/AdminReportsPage").then((m) => ({ default: m.AdminReportsPage })),
);
const AdminActivityPage = lazy(() =>
  import("@/pages/admin/AdminActivityPage").then((m) => ({ default: m.AdminActivityPage })),
);
const AdminLoginPage = lazy(() =>
  import("@/pages/admin/AdminLoginPage").then((m) => ({ default: m.AdminLoginPage })),
);

export const router = createBrowserRouter([
  {
    element: <StorefrontLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/products", element: <ProductsPage /> },
      { path: "/products/:slug", element: <ProductDetailPage /> },
      { path: "/categories", element: <CategoriesPage /> },
      { path: "/cart", element: <CartPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/403", element: <ForbiddenPage /> },
      {
        element: <RequireAuth />,
        children: [
          { path: "/checkout", element: <CheckoutPage /> },
          { path: "/checkout/result", element: <PaymentResultPage /> },
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/orders", element: <OrdersPage /> },
          { path: "/orders/:id", element: <OrderDetailPage /> },
          { path: "/wallet", element: <WalletPage /> },
          { path: "/tickets", element: <TicketsPage /> },
          { path: "/tickets/:id", element: <TicketDetailPage /> },
          { path: "/profile", element: <ProfilePage /> },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    path: "/admin/login",
    element: (
      <AdminSuspense>
        <AdminLoginPage />
      </AdminSuspense>
    ),
  },
  {
    path: "/admin",
    element: <RequireAdmin />,
    children: [
      {
        element: (
          <AdminSuspense>
            <AdminLayout />
          </AdminSuspense>
        ),
        children: [
          { index: true, element: <AdminDashboardPage /> },
          { path: "products", element: <AdminProductsPage /> },
          { path: "products/new", element: <AdminProductFormPage /> },
          { path: "products/:id/edit", element: <AdminProductFormPage /> },
          { path: "categories", element: <AdminCategoriesPage /> },
          { path: "users", element: <AdminUsersPage /> },
          { path: "users/:id", element: <AdminUserDetailPage /> },
          { path: "orders", element: <AdminOrdersPage /> },
          { path: "orders/:id", element: <AdminOrderDetailPage /> },
          { path: "tickets", element: <AdminTicketsPage /> },
          { path: "tickets/:id", element: <AdminTicketDetailPage /> },
          { path: "reports", element: <AdminReportsPage /> },
          { path: "activity", element: <AdminActivityPage /> },
        ],
      },
    ],
  },
]);
