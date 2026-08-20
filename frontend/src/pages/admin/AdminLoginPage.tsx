import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { useCurrentUser, useLogin } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

const ADMIN_ROLES = new Set(["admin", "super_admin", "support"]);

export function AdminLoginPage() {
  const { data: user, isLoading } = useCurrentUser();
  const login = useLogin();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (isLoading) return <Spinner />;
  if (user && ADMIN_ROLES.has(user.role)) return <Navigate to="/admin" replace />;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    login.mutate(
      { email, password },
      {
        onSuccess: (loggedInUser) => {
          if (!ADMIN_ROLES.has(loggedInUser.role)) {
            setError("این حساب کاربری اجازه دسترسی به پنل مدیریت را ندارد.");
            return;
          }
          navigate("/admin", { replace: true });
        },
        onError: (err) => setError(getErrorMessage(err)),
      },
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-950">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 text-center text-lg font-bold">ورود مدیریت</h1>
        <p className="mb-4 text-center text-xs text-gray-500">فروشگاه الکترونیک — پنل مدیریت</p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <Input
            label="ایمیل"
            type="email"
            ltr
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Input
            label="رمز عبور"
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" loading={login.isPending} className="w-full">
            ورود
          </Button>
        </form>
      </Card>
    </div>
  );
}
