import React from 'react'

export interface HITLQueueItem {
  id: string
  framework_code: string
  control_code: string
  control_title: string
  compliance_status: 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL' | 'NEEDS_HUMAN_REVIEW'
  risk_score: number
  confidence_score: number
  flagged_for_hitl: boolean
  evaluated_at: string
  evidence_summary: string
  advisory_hcl?: string
  azure_cli?: string
  justification_note?: string
}

interface HITLQueueTableProps {
  items: HITLQueueItem[]
  onSelectReview: (item: HITLQueueItem) => void
  selectedStatus: string
  setSelectedStatus: (status: string) => void
}

export default function HITLQueueTable({
  items,
  onSelectReview,
  selectedStatus,
  setSelectedStatus,
}: HITLQueueTableProps) {
  const getStatusBadge = (status: string, flaggedForHitl: boolean) => {
    if (flaggedForHitl || status === 'NEEDS_HUMAN_REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
          HITL PENDING REVIEW
        </span>
      )
    }
    switch (status) {
      case 'COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            COMPLIANT
          </span>
        )
      case 'NON_COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
            NON-COMPLIANT
          </span>
        )
      case 'PARTIAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-400" />
            PARTIAL
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-500/10 text-gray-400 border border-gray-500/20">
            {status}
          </span>
        )
    }
  }

  return (
    <div className="glass-card rounded-xl border border-gray-800 overflow-hidden">
      {/* Table Toolbar Header */}
      <div className="p-5 border-b border-gray-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white font-heading flex items-center gap-2">
            Audit Trail & Compliance Queue
            <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">
              {items.length} Records
            </span>
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Review automatically flagged ambiguous evidence records (&lt;85% confidence) and non-compliant control evaluations.
          </p>
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center space-x-1.5 bg-gray-900/80 p-1 rounded-lg border border-gray-800 text-xs">
          {['ALL', 'NEEDS_HUMAN_REVIEW', 'NON_COMPLIANT', 'COMPLIANT'].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                selectedStatus === st
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              {st === 'NEEDS_HUMAN_REVIEW' ? 'HITL Queue' : st}
            </button>
          ))}
        </div>
      </div>

      {/* Queue Data Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-300">
          <thead className="bg-gray-900/60 text-xs uppercase text-gray-400 font-mono border-b border-gray-800">
            <tr>
              <th className="py-3.5 px-4">Framework / Control</th>
              <th className="py-3.5 px-4">Control Requirement</th>
              <th className="py-3.5 px-4">Compliance Status</th>
              <th className="py-3.5 px-4">Risk Score</th>
              <th className="py-3.5 px-4">AI Confidence</th>
              <th className="py-3.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500">
                  No compliance records match the selected filter criteria.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="py-4 px-4 whitespace-nowrap">
                    <div className="font-mono text-xs font-bold text-blue-400">{item.framework_code}</div>
                    <div className="font-mono text-xs text-gray-200 font-semibold">{item.control_code}</div>
                  </td>
                  <td className="py-4 px-4 max-w-xs">
                    <div className="font-medium text-white line-clamp-1">{item.control_title}</div>
                    <div className="text-xs text-gray-400 line-clamp-1">{item.evidence_summary}</div>
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap">
                    {getStatusBadge(item.compliance_status, item.flagged_for_hitl)}
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap font-mono">
                    <span
                      className={`font-semibold ${
                        item.risk_score >= 7
                          ? 'text-red-400'
                          : item.risk_score >= 4
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      {item.risk_score.toFixed(2)} / 10.00
                    </span>
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap font-mono">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-semibold ${
                          item.confidence_score < 0.85 ? 'text-amber-400 font-bold' : 'text-gray-300'
                        }`}
                      >
                        {Math.round(item.confidence_score * 100)}%
                      </span>
                      {item.confidence_score < 0.85 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                          Low Confidence
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4 whitespace-nowrap text-right">
                    <button
                      onClick={() => onSelectReview(item)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        item.flagged_for_hitl || item.compliance_status === 'NEEDS_HUMAN_REVIEW'
                          ? 'bg-amber-500 text-gray-950 font-bold hover:bg-amber-400 shadow-lg shadow-amber-500/20'
                          : 'bg-gray-800 text-blue-400 hover:bg-blue-600 hover:text-white border border-gray-700'
                      }`}
                    >
                      {item.flagged_for_hitl || item.compliance_status === 'NEEDS_HUMAN_REVIEW'
                        ? 'Review & Override'
                        : 'View Details'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
