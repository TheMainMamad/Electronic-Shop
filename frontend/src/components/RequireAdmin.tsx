import { Navigate, Outlet } from "react-router-dom";

import { useCurrentUser } from "@/hooks/useAuth";
import { Spinner } from "@/components/ui/Spinner";

const ADMIN_ROLES = new Set(["admin", "super_admin", "support"]);

export function RequireAdmin() {
  const { data: user, isLoading, isError } = useCurrentUser();

  if (isLoading) return <Spinner label="در حال بررسی دسترسی شما..." />;
  if (isError || !user) return <Navigate to="/login" replace />;
  if (!ADMIN_ROLES.has(user.role)) return <Navigate to="/403" replace />;
  return <Outlet />;
}
