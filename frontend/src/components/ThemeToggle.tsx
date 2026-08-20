import { useThemeStore } from "@/stores/themeStore";
import type { ThemePreference } from "@/stores/themeStore";

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: "light", label: "روشن" },
  { value: "dark", label: "تیره" },
  { value: "system", label: "سیستم" },
];

export function ThemeToggle() {
  const { preference, setPreference } = useThemeStore();

  return (
    <div className="inline-flex rounded-lg border border-gray-200 p-0.5 dark:border-gray-700">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => setPreference(option.value)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
            preference === option.value
              ? "bg-brand-600 text-white"
              : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
