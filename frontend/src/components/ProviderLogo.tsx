import { cn } from '@/lib/utils'

type ProviderLogoProps = {
  name: string
  initials: string
  color: string
  className?: string
}

export function ProviderLogo({ name, initials, color, className }: ProviderLogoProps) {
  return (
    <div
      className={cn(
        'inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 text-xs font-semibold text-white shadow-[0_10px_30px_rgba(0,0,0,0.25)]',
        className,
      )}
      style={{
        background: `radial-gradient(circle at top, ${color}, rgba(9,9,11,0.55) 70%)`,
      }}
      aria-label={`${name} logo`}
      title={name}
    >
      {initials}
    </div>
  )
}
