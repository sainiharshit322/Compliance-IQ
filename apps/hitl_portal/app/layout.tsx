import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'ComplianceIQ - HITL Compliance Officer Review Portal',
  description: 'Human-in-the-Loop Review & Audit Override Portal for AI Compliance Automation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-gray-100 antialiased selection:bg-blue-600 selection:text-white">
        <header className="sticky top-0 z-40 border-b border-gray-800 bg-[#0b0f19]/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
              IQ
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                ComplianceIQ
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                  HITL Portal
                </span>
              </h1>
              <p className="text-xs text-gray-400">Human-in-the-Loop Compliance Officer Override Console</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs text-gray-400 bg-gray-900/60 px-3 py-1.5 rounded-lg border border-gray-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Orchestrator Gateway: <strong className="text-gray-200">Connected</strong></span>
            </div>
            <div className="text-right">
              <p className="text-xs font-semibold text-gray-200">Compliance Officer</p>
              <p className="text-[10px] font-mono text-gray-400">Role: Lead Auditor</p>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
