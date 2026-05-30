import { Github } from 'lucide-react'

type GitHubHoverButtonProps = {
  href?: string
}

export function GitHubHoverButton({ href = 'https://github.com/' }: GitHubHoverButtonProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="group inline-flex items-center gap-3 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-zinc-300 transition duration-300 hover:border-cyan-400/30 hover:bg-cyan-300/10 hover:text-white"
    >
      <span className="rounded-xl border border-white/10 bg-black/20 p-2 transition group-hover:border-cyan-400/30">
        <Github className="h-4 w-4" />
      </span>
      <span className="font-medium">GitHub</span>
    </a>
  )
}
