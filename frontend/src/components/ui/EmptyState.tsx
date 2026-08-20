import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-gray-300 py-12 text-center dark:border-gray-700">
      <p className="font-medium text-gray-700 dark:text-gray-200">{title}</p>
      {description && <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>}
      {action}
    </div>
  );
}
