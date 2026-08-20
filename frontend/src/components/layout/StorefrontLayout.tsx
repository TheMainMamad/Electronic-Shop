import { Outlet } from "react-router-dom";

import { StorefrontFooter } from "@/components/layout/StorefrontFooter";
import { StorefrontHeader } from "@/components/layout/StorefrontHeader";

export function StorefrontLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <StorefrontHeader />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <StorefrontFooter />
    </div>
  );
}
