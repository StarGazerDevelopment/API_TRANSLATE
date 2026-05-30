import { MetricCard } from '@/components/MetricCard'
import { SectionCard } from '@/components/SectionCard'
import { StatusBadge } from '@/components/StatusBadge'
import { LatencyChart, RequestsChart } from '@/components/Charts'
import { useAppStore } from '@/store/useAppStore'

export default function Dashboard() {
  const dashboard = useAppStore((state) => state.dashboard)

  if (!dashboard) {
    return <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 text-zinc-300">Loading dashboard telemetry...</div>
  }

  const metrics = [
    ['Active Providers', String(dashboard.activeProviders), 'Currently enabled gateways'],
    ['Requests Today', String(dashboard.requestsToday), 'Processed across all routes'],
    ['Requests This Month', String(dashboard.requestsThisMonth), 'Rolling total from request log'],
    ['Avg Response Time', `${dashboard.averageResponseTime} ms`, 'Measured from gateway to response'],
    ['Failed Requests', String(dashboard.failedRequests), 'Includes provider and validation failures'],
    ['Running Endpoints', String(dashboard.runningEndpoints), 'Localhost endpoints currently active'],
    ['Cache Hit Rate', `${dashboard.cacheHitRate}%`, 'Combined memory and SQLite cache effectiveness'],
    ['Failover Events', String(dashboard.failoverEvents), 'Automatic provider handoffs'],
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map(([label, value, detail]) => (
          <MetricCard key={label} label={label} value={value} detail={detail} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <RequestsChart data={dashboard.requestSeries} />
        <LatencyChart data={dashboard.latencySeries} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <SectionCard
          title="Recent Activity"
          eyebrow="Operations"
          description="Latest endpoint calls, cache decisions, and provider usage."
        >
          <div className="space-y-3">
            {dashboard.recentActivity.length === 0 ? (
              <p className="text-sm text-zinc-400">No requests logged yet. Add a provider and test an endpoint to populate activity.</p>
            ) : (
              dashboard.recentActivity.map((item) => (
                <div key={`${item.endpoint}-${item.createdAt}`} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                  <div>
                    <p className="font-medium text-white">{item.endpoint}</p>
                    <p className="text-sm text-zinc-400">
                      {item.provider ?? 'No provider'} · {new Date(item.createdAt).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="rounded-full border border-white/10 px-3 py-1 text-zinc-300">{item.statusCode}</span>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-zinc-300">{item.latencyMs} ms</span>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-zinc-300">{item.cacheHit ? 'Cache hit' : 'Fresh'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </SectionCard>

        <SectionCard title="Provider Health" eyebrow="Status" description="Health snapshots from the current provider registry.">
          <div className="space-y-3">
            {dashboard.providerHealth.map((item) => (
              <div key={item.name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <p className="text-sm font-medium text-white">{item.name}</p>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  )
}
