import { cn } from '@/lib/utils'

type StatusBadgeProps = {
  status: string
}

const statusClasses: Record<string, string> = {
  healthy: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30',
  degraded: 'bg-amber-500/15 text-amber-300 border-amber-400/30',
  unknown: 'bg-zinc-500/15 text-zinc-300 border-zinc-400/30',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium capitalize',
        statusClasses[status] ?? statusClasses.unknown,
      )}
    >
      {status.replace('_', ' ')}
    </span>
  )
}
