import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <span className="text-5xl font-bold text-gray-300 dark:text-gray-700">۴۰۴</span>
      <h1 className="text-lg font-bold">صفحه موردنظر پیدا نشد</h1>
      <p className="text-sm text-gray-500">آدرسی که وارد کرده‌اید وجود ندارد یا جابه‌جا شده است.</p>
      <Link to="/" className="text-brand-600 hover:underline">
        بازگشت به صفحه اصلی
      </Link>
    </div>
  );
}
