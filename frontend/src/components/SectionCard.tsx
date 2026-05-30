import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type SectionCardProps = {
  title: string
  eyebrow?: string
  description?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
}

export function SectionCard({ title, eyebrow, description, actions, children, className }: SectionCardProps) {
  return (
    <section
      className={cn(
        'rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.08),_transparent_45%),linear-gradient(180deg,rgba(24,24,27,0.96),rgba(10,10,15,0.96))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.35)] backdrop-blur transition duration-300 hover:border-cyan-400/20 hover:shadow-[0_30px_90px_rgba(34,211,238,0.08)]',
        className,
      )}
    >
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          {eyebrow ? <p className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">{eyebrow}</p> : null}
          <div>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
            {description ? <p className="mt-1 text-sm text-zinc-400">{description}</p> : null}
          </div>
        </div>
        {actions}
      </div>
      {children}
    </section>
  )
}
