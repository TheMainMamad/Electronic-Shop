import { useThemeStore } from "@/stores/themeStore";

const themeLabels: Record<string, string> = {
  light: "روشن",
  dark: "تیره",
  system: "سیستم",
};

function App() {
  const { preference, setPreference } = useThemeStore();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-2xl font-bold">فروشگاه الکترونیک</h1>
      <p className="text-gray-500 dark:text-gray-400">
        زیرساخت پروژه آماده شد؛ صفحات فروشگاه در فازهای بعدی تکمیل می‌شوند.
      </p>
      <div className="flex gap-2">
        {(Object.keys(themeLabels) as Array<keyof typeof themeLabels>).map((key) => (
          <button
            key={key}
            onClick={() => setPreference(key as never)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              preference === key
                ? "bg-brand-600 text-white"
                : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200"
            }`}
          >
            {themeLabels[key]}
          </button>
        ))}
      </div>
    </div>
  );
}

export default App;
