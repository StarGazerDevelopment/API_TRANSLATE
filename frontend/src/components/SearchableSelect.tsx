import { useMemo, useState } from 'react'
import { Check, ChevronDown, Search } from 'lucide-react'

import { cn } from '@/lib/utils'

type SearchableSelectProps = {
  label: string
  value: string
  options: string[]
  placeholder?: string
  onChange: (value: string) => void
}

export function SearchableSelect({
  label,
  value,
  options,
  placeholder = 'Search options',
  onChange,
}: SearchableSelectProps) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) {
      return options
    }
    return options.filter((option) => option.toLowerCase().includes(normalized))
  }, [options, query])

  return (
    <div className="relative">
      <label className="block text-sm text-zinc-300">{label}</label>
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="mt-2 flex w-full items-center justify-between rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-left text-white outline-none transition hover:border-cyan-400/30"
      >
        <span className={cn('truncate', !value && 'text-zinc-500')}>{value || placeholder}</span>
        <ChevronDown className={cn('h-4 w-4 text-zinc-400 transition', open && 'rotate-180')} />
      </button>

      {open ? (
        <div className="absolute z-30 mt-2 w-full rounded-3xl border border-white/10 bg-[#0b0b11]/95 p-3 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur">
          <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2">
            <Search className="h-4 w-4 text-zinc-500" />
            <input
              autoFocus
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={placeholder}
              className="w-full bg-transparent text-sm text-white outline-none placeholder:text-zinc-500"
            />
          </div>
          <div className="mt-3 max-h-64 overflow-auto">
            {filtered.length === 0 ? (
              <div className="rounded-2xl px-3 py-4 text-sm text-zinc-500">No matching models.</div>
            ) : (
              filtered.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => {
                    onChange(option)
                    setOpen(false)
                    setQuery('')
                  }}
                  className="flex w-full items-center justify-between rounded-2xl px-3 py-3 text-left text-sm text-zinc-200 transition hover:bg-white/[0.05]"
                >
                  <span className="truncate">{option}</span>
                  {value === option ? <Check className="h-4 w-4 text-cyan-300" /> : null}
                </button>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
