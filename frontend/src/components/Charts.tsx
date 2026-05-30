import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { SectionCard } from '@/components/SectionCard'

type SeriesPoint = {
  label: string
  requests?: number
  latency?: number
}

export function RequestsChart({ data }: { data: SeriesPoint[] }) {
  return (
    <SectionCard title="Requests" eyebrow="Telemetry" description="Live request rhythm across the latest gateway activity window.">
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#a1a1aa', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#71717a', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#111116', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 16 }} />
            <Bar dataKey="requests" radius={[10, 10, 0, 0]}>
              {data.map((_, index) => (
                <Cell key={`request-${index}`} fill={index % 2 === 0 ? '#22d3ee' : '#8b5cf6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  )
}

export function LatencyChart({ data }: { data: SeriesPoint[] }) {
  return (
    <SectionCard title="Latency" eyebrow="Performance" description="Average provider response timing from the gateway log stream.">
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#a1a1aa', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#71717a', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#111116', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 16 }} />
            <Line type="monotone" dataKey="latency" stroke="#22d3ee" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  )
}
