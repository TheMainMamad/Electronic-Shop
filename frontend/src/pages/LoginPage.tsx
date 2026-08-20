import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { googleLoginUrl } from "@/api/auth";
import { useLogin } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export function LoginPage() {
  const login = useLogin();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const redirectTo = (location.state as { from?: string } | null)?.from ?? "/dashboard";

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    login.mutate(
      { email, password },
      {
        onSuccess: () => navigate(redirectTo, { replace: true }),
        onError: (err) => setError(getErrorMessage(err)),
      },
    );
  };

  return (
    <div className="mx-auto max-w-sm py-8">
      <Card>
        <h1 className="mb-4 text-center text-lg font-bold">ورود به حساب کاربری</h1>
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

        <div className="my-4 flex items-center gap-2 text-xs text-gray-400">
          <span className="h-px flex-1 bg-gray-200 dark:bg-gray-800" />
          یا
          <span className="h-px flex-1 bg-gray-200 dark:bg-gray-800" />
        </div>

        <a
          href={googleLoginUrl()}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
        >
          ورود با گوگل
        </a>

        <p className="mt-4 text-center text-sm text-gray-500">
          حساب کاربری ندارید؟{" "}
          <Link to="/register" className="text-brand-600 hover:underline">
            ثبت‌نام کنید
          </Link>
        </p>
      </Card>
    </div>
  );
}
