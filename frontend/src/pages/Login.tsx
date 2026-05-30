import { useState } from 'react'
import { Navigate } from 'react-router-dom'

import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export default function LoginPage() {
  const authenticated = useAppStore((state) => state.authenticated)
  const protectedMode = useAppStore((state) => state.protectedMode)
  const bootstrap = useAppStore((state) => state.bootstrap)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  if (!protectedMode) {
    return <Navigate to="/" replace />
  }

  if (authenticated) {
    return <Navigate to="/" replace />
  }

  const submit = async () => {
    try {
      await api.login(password)
      await bootstrap()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Login failed.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#09090b] px-4 text-zinc-100">
      <div className="w-full max-w-md rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(24,24,27,0.96),rgba(10,10,15,0.96))] p-8 shadow-[0_30px_120px_rgba(0,0,0,0.45)]">
        <p className="text-xs uppercase tracking-[0.34em] text-cyan-300/80">Protected Dashboard</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Welcome Back</h1>
        <p className="mt-3 text-sm text-zinc-400">Enter the local admin password to manage providers, logs, settings, and generated endpoints.</p>
        <label className="mt-6 block text-sm text-zinc-300">
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
        </label>
        <button onClick={() => void submit()} className="mt-5 w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950 transition hover:opacity-90">
          Unlock Dashboard
        </button>
        {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
      </div>
    </div>
  )
}
