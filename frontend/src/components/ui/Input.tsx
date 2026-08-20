import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

interface FieldWrapperProps {
  label?: string;
  error?: string;
  hint?: string;
  ltr?: boolean;
}

const BASE_CLASSES =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:placeholder:text-gray-500 dark:disabled:bg-gray-800";

export function Input({
  label,
  error,
  hint,
  ltr,
  className = "",
  ...rest
}: FieldWrapperProps & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
      <input
        className={`${BASE_CLASSES} ${ltr ? "ltr-inline text-left" : ""} ${error ? "border-red-500" : ""} ${className}`}
        {...rest}
      />
      {hint && !error && <span className="mt-1 block text-xs text-gray-500">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}

export function Textarea({
  label,
  error,
  hint,
  className = "",
  ...rest
}: FieldWrapperProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
      <textarea className={`${BASE_CLASSES} ${error ? "border-red-500" : ""} ${className}`} {...rest} />
      {hint && !error && <span className="mt-1 block text-xs text-gray-500">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}
