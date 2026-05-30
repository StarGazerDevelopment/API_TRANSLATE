type MetricCardProps = {
  label: string
  value: string
  detail: string
}

export function MetricCard({ label, value, detail }: MetricCardProps) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 transition duration-300 hover:border-cyan-400/30 hover:bg-white/[0.05]">
      <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">{label}</p>
      <p className="mt-4 bg-gradient-to-r from-white to-cyan-200 bg-clip-text text-3xl font-semibold text-transparent">
        {value}
      </p>
      <p className="mt-2 text-sm text-zinc-400">{detail}</p>
    </div>
  )
}
