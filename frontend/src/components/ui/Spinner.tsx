export function Spinner({ label = "در حال بارگذاری..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-gray-500 dark:text-gray-400">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-current border-t-transparent" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
