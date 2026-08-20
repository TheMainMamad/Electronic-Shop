import { Link } from "react-router-dom";

export function ForbiddenPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <span className="text-5xl font-bold text-gray-300 dark:text-gray-700">۴۰۳</span>
      <h1 className="text-lg font-bold">شما اجازه دسترسی به این بخش را ندارید</h1>
      <p className="text-sm text-gray-500">اگر فکر می‌کنید این یک اشتباه است، با پشتیبانی تماس بگیرید.</p>
      <Link to="/" className="text-brand-600 hover:underline">
        بازگشت به صفحه اصلی
      </Link>
    </div>
  );
}
