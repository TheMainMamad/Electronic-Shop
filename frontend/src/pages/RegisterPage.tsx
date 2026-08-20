import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useRegister } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export function RegisterPage() {
  const registerMutation = useRegister();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    first_name: "",
    last_name: "",
  });
  const [error, setError] = useState("");

  const update = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }));

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    registerMutation.mutate(form, {
      onSuccess: () => navigate("/dashboard", { replace: true }),
      onError: (err) => setError(getErrorMessage(err)),
    });
  };

  return (
    <div className="mx-auto max-w-sm py-8">
      <Card>
        <h1 className="mb-4 text-center text-lg font-bold">ثبت‌نام</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <Input label="نام" value={form.first_name} onChange={update("first_name")} />
            <Input label="نام خانوادگی" value={form.last_name} onChange={update("last_name")} />
          </div>
          <Input
            label="نام کاربری"
            required
            minLength={3}
            value={form.username}
            onChange={update("username")}
            ltr
            hint="فقط حروف انگلیسی، عدد و زیرخط"
          />
          <Input label="ایمیل" type="email" required ltr value={form.email} onChange={update("email")} />
          <Input
            label="رمز عبور"
            type="password"
            required
            minLength={8}
            value={form.password}
            onChange={update("password")}
            hint="حداقل ۸ کاراکتر، ترکیبی از حروف و اعداد"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" loading={registerMutation.isPending} className="w-full">
            ثبت‌نام
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
          قبلاً ثبت‌نام کرده‌اید؟{" "}
          <Link to="/login" className="text-brand-600 hover:underline">
            وارد شوید
          </Link>
        </p>
      </Card>
    </div>
  );
}
