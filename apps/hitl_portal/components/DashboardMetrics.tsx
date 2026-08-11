import React from 'react'

interface DashboardMetricsProps {
  totalControls: number
  compliantCount: number
  pendingHITLCount: number
  criticalGapsCount: number
}

export default function DashboardMetrics({
  totalControls = 15,
  compliantCount = 11,
  pendingHITLCount = 3,
  criticalGapsCount = 1,
}: DashboardMetricsProps) {
  const complianceRate = Math.round((compliantCount / (totalControls || 1)) * 100)

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
      {/* 1. Compliance Rate Card */}
      <div className="glass-card p-5 rounded-xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 text-blue-400 group-hover:scale-110 transition-transform">
          <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
        </div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Overall Compliance Rate</p>
        <div className="mt-2 flex items-baseline gap-3">
          <span className="text-3xl font-extrabold text-white font-heading">{complianceRate}%</span>
          <span className="text-xs text-emerald-400 font-medium">↑ +4% from last scan</span>
        </div>
        <div className="w-full bg-gray-800 h-1.5 rounded-full mt-4 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-emerald-400 h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${complianceRate}%` }}
          />
        </div>
      </div>

      {/* 2. Pending HITL Review Queue */}
      <div className="glass-card p-5 rounded-xl relative overflow-hidden group border-amber-500/30">
        <div className="absolute top-0 right-0 p-4 opacity-10 text-amber-400 group-hover:scale-110 transition-transform">
          <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
        </div>
        <p className="text-xs font-medium text-amber-400 uppercase tracking-wider">Pending HITL Reviews</p>
        <div className="mt-2 flex items-baseline gap-3">
          <span className="text-3xl font-extrabold text-amber-300 font-heading">{pendingHITLCount}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">Action Required</span>
        </div>
        <p className="text-xs text-gray-400 mt-4">Guardrail 2: AI Confidence &lt; 85%</p>
      </div>

      {/* 3. Total Evaluated Controls */}
      <div className="glass-card p-5 rounded-xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 text-indigo-400 group-hover:scale-110 transition-transform">
          <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
          </svg>
        </div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Evaluated Controls</p>
        <div className="mt-2 flex items-baseline gap-3">
          <span className="text-3xl font-extrabold text-white font-heading">{totalControls}</span>
          <span className="text-xs text-gray-400">Across 5 Frameworks</span>
        </div>
        <p className="text-xs text-emerald-400 mt-4">{compliantCount} Passed Automatically</p>
      </div>

      {/* 4. Critical Risk Gaps */}
      <div className="glass-card p-5 rounded-xl relative overflow-hidden group border-red-500/30">
        <div className="absolute top-0 right-0 p-4 opacity-10 text-red-400 group-hover:scale-110 transition-transform">
          <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L1 21h22L12 2zm1 14h-2v-2h2v2zm0-4h-2v-4h2v4z" />
          </svg>
        </div>
        <p className="text-xs font-medium text-red-400 uppercase tracking-wider">Critical Risk Gaps</p>
        <div className="mt-2 flex items-baseline gap-3">
          <span className="text-3xl font-extrabold text-red-400 font-heading">{criticalGapsCount}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-mono">High Priority</span>
        </div>
        <p className="text-xs text-gray-400 mt-4">Advisory Terraform HCL Generated</p>
      </div>
    </div>
  )
}
