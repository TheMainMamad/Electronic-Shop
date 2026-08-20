import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card } from "@/components/ui/Card";
import { useIsDark } from "@/hooks/useIsDark";
import { categoricalPalette, chartInk } from "@/lib/chartPalette";
import { formatJalaliDate, formatNumber } from "@/lib/persian";

export function TrendChartCard({
  title,
  data,
  valueFormatter,
}: {
  title: string;
  data: { date: string; value: number }[];
  valueFormatter?: (value: number) => string;
}) {
  const isDark = useIsDark();
  const ink = chartInk(isDark);
  const color = categoricalPalette(isDark)[0];
  const format = valueFormatter ?? formatNumber;

  return (
    <Card>
      <h3 className="mb-3 text-sm font-bold text-gray-700 dark:text-gray-200">{title}</h3>
      <div className="h-56 w-full ltr-inline" dir="ltr">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={ink.grid} vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={(value: string) => formatJalaliDate(value)}
              tick={{ fontSize: 11, fill: ink.muted }}
              tickLine={false}
              axisLine={{ stroke: ink.grid }}
              minTickGap={24}
            />
            <YAxis
              tick={{ fontSize: 11, fill: ink.muted }}
              tickLine={false}
              axisLine={false}
              width={44}
              tickFormatter={(value: number) => formatNumber(value)}
            />
            <Tooltip
              formatter={(value) => format(Number(value))}
              labelFormatter={(value) => formatJalaliDate(String(value))}
              contentStyle={{
                background: isDark ? "#1a1a19" : "#fcfcfb",
                border: `1px solid ${ink.grid}`,
                borderRadius: 8,
                fontSize: 12,
                direction: "rtl",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
