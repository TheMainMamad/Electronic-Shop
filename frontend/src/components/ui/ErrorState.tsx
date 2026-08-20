export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
      {message}
    </div>
  );
}
