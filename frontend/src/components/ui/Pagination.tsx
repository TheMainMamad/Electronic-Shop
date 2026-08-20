import { toPersianDigits } from "@/lib/persian";
import { Button } from "@/components/ui/Button";

export function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-3 py-4">
      <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        قبلی
      </Button>
      <span className="text-sm text-gray-600 dark:text-gray-300">
        صفحه {toPersianDigits(page)} از {toPersianDigits(totalPages)}
      </span>
      <Button
        variant="secondary"
        size="sm"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        بعدی
      </Button>
    </div>
  );
}
