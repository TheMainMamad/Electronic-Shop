// Validated categorical palette (see dataviz skill references/palette.md).
// Fixed hue order — never cycled or reassigned per-render.
export const CATEGORICAL_LIGHT = [
  "#2a78d6", // blue
  "#eb6834", // orange
  "#1baf7a", // aqua
  "#eda100", // yellow
  "#e87ba4", // magenta
  "#008300", // green
  "#4a3aa7", // violet
  "#e34948", // red
];

export const CATEGORICAL_DARK = [
  "#3987e5",
  "#d95926",
  "#199e70",
  "#c98500",
  "#d55181",
  "#008300",
  "#9085e9",
  "#e66767",
];

export const CHART_INK_LIGHT = { primary: "#0b0b0b", secondary: "#52514e", muted: "#898781", grid: "#e1e0d9" };
export const CHART_INK_DARK = { primary: "#ffffff", secondary: "#c3c2b7", muted: "#898781", grid: "#2c2c2a" };

export function categoricalPalette(isDark: boolean): string[] {
  return isDark ? CATEGORICAL_DARK : CATEGORICAL_LIGHT;
}

export function chartInk(isDark: boolean) {
  return isDark ? CHART_INK_DARK : CHART_INK_LIGHT;
}

// Colors are assigned per-entity (by a stable hash of its label), not by
// array position — so a given status/category keeps the same color across
// renders even as other slices appear or disappear around it.
export function colorForLabel(label: string, isDark: boolean): string {
  let hash = 0;
  for (let i = 0; i < label.length; i++) {
    hash = (hash * 31 + label.charCodeAt(i)) >>> 0;
  }
  const palette = categoricalPalette(isDark);
  return palette[hash % palette.length];
}
