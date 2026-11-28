"use client";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { palette } from "@/config/theme";

export interface Point { name: string; value: number }

const axis = { fill: palette.muted, fontSize: 11 };
const tooltip = { background: "#fff", color: palette.navy, borderRadius: 8, border: `1px solid ${palette.gold}` };

export function BarCard({ data, horizontal = false, height = 260, highlight }: { data: Point[]; horizontal?: boolean; height?: number; highlight?: string }) {
  const h = horizontal ? Math.max(height, data.length * 34 + 30) : height;
  return (
    <div dir="ltr" style={{ width: "100%", height: h }}>
      <ResponsiveContainer>
        <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ left: horizontal ? 10 : 0, right: 12, top: 4 }}>
          <CartesianGrid stroke={palette.line} strokeDasharray="3 3" />
          {horizontal ? (
            <>
              <XAxis type="number" tick={axis} />
              <YAxis type="category" dataKey="name" width={110} tick={axis} />
            </>
          ) : (
            <>
              <XAxis dataKey="name" tick={axis} interval="preserveStartEnd" />
              <YAxis tick={axis} width={44} />
            </>
          )}
          <Tooltip contentStyle={tooltip} cursor={{ fill: palette.goldSoft }} />
          <Bar dataKey="value" radius={3}>
            {data.map((d) => <Cell key={d.name} fill={highlight === d.name ? palette.gold : palette.navy} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LineCard({ data, height = 260 }: { data: Point[]; height?: number }) {
  return (
    <div dir="ltr" style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ right: 12, top: 4 }}>
          <CartesianGrid stroke={palette.line} strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={axis} interval="preserveStartEnd" />
          <YAxis tick={axis} width={44} />
          <Tooltip contentStyle={tooltip} />
          <Line type="monotone" dataKey="value" stroke={palette.gold} strokeWidth={2.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
