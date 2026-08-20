import { create } from "zustand";

export type ThemePreference = "light" | "dark" | "system";

function resolveIsDark(preference: ThemePreference): boolean {
  if (preference === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  return preference === "dark";
}

function applyTheme(isDark: boolean): void {
  document.documentElement.classList.toggle("dark", isDark);
}

interface ThemeState {
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
}

const initialPreference = (localStorage.getItem("theme") as ThemePreference | null) ?? "system";
applyTheme(resolveIsDark(initialPreference));

export const useThemeStore = create<ThemeState>((set) => ({
  preference: initialPreference,
  setPreference: (preference) => {
    localStorage.setItem("theme", preference);
    applyTheme(resolveIsDark(preference));
    set({ preference });
  },
}));
