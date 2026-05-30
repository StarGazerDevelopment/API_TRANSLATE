import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/AppShell'
import ApiKeysPage from '@/pages/ApiKeys'
import BuilderPage from '@/pages/Builder'
import Dashboard from '@/pages/Dashboard'
import DeploymentsPage from '@/pages/Deployments'
import DocumentationPage from '@/pages/Documentation'
import LoginPage from '@/pages/Login'
import LogsPage from '@/pages/Logs'
import Providers from '@/pages/Providers'
import SettingsPage from '@/pages/Settings'
import { useAppStore } from '@/store/useAppStore'

function ProtectedLayout() {
  const bootstrap = useAppStore((state) => state.bootstrap)
  const authenticated = useAppStore((state) => state.authenticated)
  const protectedMode = useAppStore((state) => state.protectedMode)
  const loading = useAppStore((state) => state.loading)
  const error = useAppStore((state) => state.error)

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-[#09090b] text-zinc-300">Loading AI-Translator...</div>
  }

  if (protectedMode && !authenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <AppShell>
      {error ? <div className="mb-6 rounded-3xl border border-rose-400/20 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">{error}</div> : null}
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/providers" element={<Providers />} />
        <Route path="/api-keys" element={<ApiKeysPage />} />
        <Route path="/builder" element={<BuilderPage />} />
        <Route path="/deployments" element={<DeploymentsPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/docs" element={<DocumentationPage />} />
      </Routes>
    </AppShell>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<ProtectedLayout />} />
      </Routes>
    </BrowserRouter>
  )
}
