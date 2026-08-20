import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { changePassword } from "@/api/auth";
import { useCurrentUser } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/errors";
import { userRoleLabels } from "@/lib/statusLabels";
import { useToastStore } from "@/stores/toastStore";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";

export function ProfilePage() {
  const { data: user } = useCurrentUser();
  const push = useToastStore((state) => state.push);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const submit = useMutation({
    mutationFn: () => changePassword(currentPassword, newPassword),
    onSuccess: () => {
      push("رمز عبور با موفقیت تغییر کرد. لطفاً دوباره وارد شوید.", "success");
      setCurrentPassword("");
      setNewPassword("");
    },
    onError: (err) => push(getErrorMessage(err), "error"),
  });

  if (!user) return <Spinner />;

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6">
      <h1 className="text-xl font-bold">پروفایل کاربری</h1>

      <Card>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <dt className="text-gray-500">نام</dt>
          <dd>{user.first_name || "—"}</dd>
          <dt className="text-gray-500">نام خانوادگی</dt>
          <dd>{user.last_name || "—"}</dd>
          <dt className="text-gray-500">نام کاربری</dt>
          <dd className="ltr-inline">{user.username}</dd>
          <dt className="text-gray-500">ایمیل</dt>
          <dd className="ltr-inline">{user.email}</dd>
          <dt className="text-gray-500">نقش</dt>
          <dd>{userRoleLabels[user.role]}</dd>
        </dl>
      </Card>

      <Card>
        <h2 className="mb-3 font-bold">تغییر رمز عبور</h2>
        <form
          className="flex flex-col gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            submit.mutate();
          }}
        >
          <Input
            label="رمز عبور فعلی"
            type="password"
            required
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
          <Input
            label="رمز عبور جدید"
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
          <Button type="submit" loading={submit.isPending} className="w-fit">
            تغییر رمز عبور
          </Button>
        </form>
      </Card>
    </div>
  );
}
