import { useToastStore } from "@/stores/toastStore";

const TONE_CLASSES: Record<string, string> = {
  success: "bg-emerald-600",
  error: "bg-red-600",
  info: "bg-gray-800 dark:bg-gray-700",
};

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={`pointer-events-auto max-w-md rounded-lg px-4 py-2.5 text-sm text-white shadow-lg ${TONE_CLASSES[toast.tone]}`}
          onClick={() => dismiss(toast.id)}
        >
          {toast.text}
        </div>
      ))}
    </div>
  );
}
