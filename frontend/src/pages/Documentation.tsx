import { SectionCard } from '@/components/SectionCard'
import { useAppStore } from '@/store/useAppStore'

export default function DocumentationPage() {
  const sections = useAppStore((state) => state.docs)

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <SectionCard key={section.title} title={section.title} eyebrow="Generated Docs">
          <div className="space-y-3">
            {section.content.map((line) => (
              <pre key={line} className="overflow-auto rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-sm text-cyan-100">
                {line}
              </pre>
            ))}
          </div>
        </SectionCard>
      ))}
      {sections.length === 0 ? <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 text-zinc-400">Documentation will appear here after the backend loads generated endpoint and provider docs.</div> : null}
    </div>
  )
}
