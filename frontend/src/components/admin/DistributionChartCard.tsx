import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { Card } from "@/components/ui/Card";
import { useIsDark } from "@/hooks/useIsDark";
import { colorForLabel } from "@/lib/chartPalette";
import { EmptyState } from "@/components/ui/EmptyState";
import { toPersianDigits } from "@/lib/persian";

export function DistributionChartCard({
  title,
  data,
  labelMap,
}: {
  title: string;
  data: { label: string; count: number }[];
  labelMap?: Record<string, string>;
}) {
  const isDark = useIsDark();
  const total = data.reduce((sum, item) => sum + item.count, 0);

  const chartData = data.map((item) => ({
    key: item.label,
    name: labelMap?.[item.label] ?? item.label,
    value: item.count,
  }));

  return (
    <Card>
      <h3 className="mb-3 text-sm font-bold text-gray-700 dark:text-gray-200">{title}</h3>
      {total === 0 ? (
        <EmptyState title="داده‌ای برای نمایش وجود ندارد." />
      ) : (
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius="55%"
                outerRadius="85%"
                paddingAngle={2}
                strokeWidth={2}
                stroke={isDark ? "#1a1a19" : "#fcfcfb"}
              >
                {chartData.map((entry) => (
                  <Cell key={entry.key} fill={colorForLabel(entry.key, isDark)} />
                ))}
              </Pie>
              <Legend
                layout="vertical"
                align="left"
                verticalAlign="middle"
                wrapperStyle={{ fontSize: 12, direction: "rtl" }}
              />
              <Tooltip
                formatter={(value, name) => [`${toPersianDigits(Number(value))} مورد`, String(name)]}
                contentStyle={{
                  background: isDark ? "#1a1a19" : "#fcfcfb",
                  border: `1px solid ${isDark ? "#2c2c2a" : "#e1e0d9"}`,
                  borderRadius: 8,
                  fontSize: 12,
                  direction: "rtl",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
