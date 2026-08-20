import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useCurrentUser } from "@/hooks/useAuth";
import { Spinner } from "@/components/ui/Spinner";

export function RequireAuth() {
  const { data: user, isLoading, isError } = useCurrentUser();
  const location = useLocation();

  if (isLoading) return <Spinner label="در حال بررسی نشست شما..." />;
  if (isError || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
