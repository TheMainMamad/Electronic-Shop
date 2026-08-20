import { Suspense } from "react";
import type { ReactNode } from "react";

import { Spinner } from "@/components/ui/Spinner";

export function AdminSuspense({ children }: { children: ReactNode }) {
  return <Suspense fallback={<Spinner label="در حال بارگذاری پنل مدیریت..." />}>{children}</Suspense>;
}
