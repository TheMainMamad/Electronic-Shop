import { Card } from "@/components/ui/Card";
import { toPersianDigits } from "@/lib/persian";

export function StatCard({
  label,
  value,
  formatted,
}: {
  label: string;
  value?: number;
  formatted?: string;
}) {
  return (
    <Card>
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-gray-900 dark:text-gray-100">
        {formatted ?? (value !== undefined ? toPersianDigits(value) : "—")}
      </p>
    </Card>
  );
}
