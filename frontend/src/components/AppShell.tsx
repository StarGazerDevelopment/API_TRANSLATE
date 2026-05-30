import { type ReactNode, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Activity,
  BookOpenText,
  Bot,
  Boxes,
  Cable,
  FileCode2,
  KeyRound,
  LayoutDashboard,
  Settings2,
} from 'lucide-react'

import { GitHubHoverButton } from '@/components/GitHubHoverButton'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/providers', label: 'Providers', icon: Bot },
  { to: '/api-keys', label: 'API Keys', icon: KeyRound },
  { to: '/builder', label: 'API Builder', icon: Cable },
  { to: '/deployments', label: 'Build', icon: Boxes },
  { to: '/logs', label: 'Logs', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings2 },
  { to: '/docs', label: 'Documentation', icon: BookOpenText },
]

type AppShellProps = {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const activeSection = useMemo(
    () => navItems.find((item) => item.to === location.pathname)?.label ?? 'Control Center',
    [location.pathname],
  )

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,_rgba(6,182,212,0.15),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(139,92,246,0.12),_transparent_28%)]" />
      <div className="relative mx-auto flex min-h-screen max-w-[1800px] gap-6 px-4 py-4 lg:px-6">
        <aside className="hidden w-[280px] shrink-0 rounded-[32px] border border-white/10 bg-white/[0.03] p-5 shadow-2xl backdrop-blur lg:flex lg:flex-col">
          <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/5 p-4">
            <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/80">API Gateway</p>
            <h1 className="mt-2 text-xl font-semibold text-white">AI-Translator</h1>
            <p className="mt-4 text-sm text-zinc-300">
              Simple local AI routing, saved flows, and deployable endpoints.
            </p>
          </div>

          <nav className="mt-6 flex-1 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = location.pathname === item.to
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    'flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition duration-200',
                    active
                      ? 'border-cyan-400/35 bg-cyan-300/10 text-white shadow-[0_0_40px_rgba(34,211,238,0.12)]'
                      : 'border-transparent bg-white/[0.02] text-zinc-400 hover:border-white/10 hover:bg-white/[0.05] hover:text-zinc-100',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          <div className="rounded-3xl border border-white/10 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Focus</p>
            <p className="mt-3 text-sm text-zinc-300">Expose OpenAI-compatible endpoints for apps, games, scripts, and desktops with one deployable local gateway.</p>
            <div className="mt-4">
              <GitHubHoverButton />
            </div>
          </div>
        </aside>

        <main className="flex-1">
          <div className="mb-6 flex items-center justify-between rounded-[32px] border border-white/10 bg-white/[0.03] px-6 py-5 backdrop-blur">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-zinc-500">Workspace</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">{activeSection}</h2>
            </div>
            <div className="flex items-center gap-3 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-200">
              <FileCode2 className="h-4 w-4" />
              AI-Translator
            </div>
          </div>

          <div className="mb-6 overflow-x-auto rounded-[28px] border border-white/10 bg-white/[0.03] p-3 backdrop-blur">
            <div className="flex min-w-max gap-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const active = location.pathname === item.to
                return (
                  <Link
                    key={`tab-${item.to}`}
                    to={item.to}
                    className={cn(
                      'inline-flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-medium transition duration-200',
                      active
                        ? 'border-cyan-400/35 bg-gradient-to-r from-cyan-300/15 to-violet-400/15 text-white shadow-[0_0_30px_rgba(34,211,238,0.12)]'
                        : 'border-transparent bg-white/[0.02] text-zinc-400 hover:border-white/10 hover:bg-white/[0.05] hover:text-zinc-100',
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>

          {children}
        </main>
      </div>
    </div>
  )
}
