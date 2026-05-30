import { SectionCard } from '@/components/SectionCard'
import { useAppStore } from '@/store/useAppStore'

export default function LogsPage() {
  const logs = useAppStore((state) => state.logs)

  return (
    <SectionCard title="Request Logs" eyebrow="Audit" description="Searchable operational history with latency, failover, cache, and provider details.">
      <div className="overflow-hidden rounded-3xl border border-white/10">
        <div className="grid grid-cols-[1.2fr_0.8fr_0.4fr_0.5fr_0.5fr_0.8fr] gap-3 bg-white/[0.04] px-4 py-3 text-xs uppercase tracking-[0.24em] text-zinc-500">
          <span>Endpoint</span>
          <span>Provider</span>
          <span>Status</span>
          <span>Latency</span>
          <span>Cache</span>
          <span>Time</span>
        </div>
        <div className="max-h-[620px] overflow-auto">
          {logs.map((log) => (
            <div key={log.id} className="grid grid-cols-[1.2fr_0.8fr_0.4fr_0.5fr_0.5fr_0.8fr] gap-3 border-t border-white/10 px-4 py-3 text-sm text-zinc-300">
              <span className="truncate">{log.endpointPath}</span>
              <span className="truncate">{log.providerSlug ?? 'n/a'}</span>
              <span>{log.statusCode}</span>
              <span>{log.latencyMs} ms</span>
              <span>{log.cacheHit ? 'hit' : 'miss'}</span>
              <span>{new Date(log.createdAt).toLocaleString()}</span>
            </div>
          ))}
          {logs.length === 0 ? <div className="px-4 py-10 text-sm text-zinc-400">No request logs yet.</div> : null}
        </div>
      </div>
    </SectionCard>
  )
}
