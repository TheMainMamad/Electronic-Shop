import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { googleLoginUrl } from "@/api/auth";
import { useLogin } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48">
      <path
        fill="#EA4335"
        d="M24 9.5c3.4 0 6.4 1.2 8.8 3.4l6.5-6.5C35.3 2.6 30 0.5 24 0.5 14.9 0.5 7.1 5.7 3.3 13.3l7.6 5.9C12.7 13.4 17.9 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.5 3-2.2 5.5-4.7 7.2l7.3 5.7c4.3-4 6.8-9.8 6.8-17.4z"
      />
      <path
        fill="#FBBC05"
        d="M10.9 28.2a14.5 14.5 0 0 1 0-8.4l-7.6-5.9a24 24 0 0 0 0 20.2l7.6-5.9z"
      />
      <path
        fill="#34A853"
        d="M24 47.5c6 0 11.3-2 15.1-5.4l-7.3-5.7c-2 1.4-4.7 2.2-7.8 2.2-6.1 0-11.3-3.9-13.2-9.4l-7.6 5.9C7.1 42.3 14.9 47.5 24 47.5z"
      />
    </svg>
  );
}

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
          <GoogleIcon />
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
