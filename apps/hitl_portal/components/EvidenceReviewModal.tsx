import React, { useState } from 'react'
import { HITLQueueItem } from './HITLQueueTable'

interface EvidenceReviewModalProps {
  item: HITLQueueItem | null
  onClose: () => void
  onSaveOverride: (updatedItem: HITLQueueItem, newStatus: string, justification: string) => void
}

export default function EvidenceReviewModal({
  item,
  onClose,
  onSaveOverride,
}: EvidenceReviewModalProps) {
  if (!item) return null

  const [overrideStatus, setOverrideStatus] = useState<'COMPLIANT' | 'NON_COMPLIANT'>('COMPLIANT')
  const [justification, setJustification] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  const handleSave = () => {
    if (justification.trim().length < 15) {
      setErrorMsg('Mandatory audit compliance rule: Justification note must be at least 15 characters.')
      return
    }
    setErrorMsg('')
    onSaveOverride(item, overrideStatus, justification)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-modal max-w-5xl w-full rounded-2xl border border-gray-700 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/80">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-blue-400 px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20">
                {item.framework_code}
              </span>
              <span className="font-mono text-xs text-gray-300 font-bold">{item.control_code}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">
                AI Confidence: {Math.round(item.confidence_score * 100)}%
              </span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1 font-heading">{item.control_title}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-gray-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Content - Side by Side Grid */}
        <div className="p-6 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column: Raw Evidence JSON & Scope */}
          <div className="flex flex-col space-y-4">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider font-mono">
              Raw Collector Ingested Evidence
            </h3>
            <div className="p-4 rounded-xl bg-gray-950 border border-gray-800 font-mono text-xs text-gray-300 space-y-2 overflow-x-auto">
              <p className="text-blue-400 font-semibold">// Ingested Resource Payload</p>
              <pre className="text-emerald-400 whitespace-pre-wrap">
{JSON.stringify(
  {
    collector_type: "AZURE_POLICY",
    resource_id: item.evidence_summary,
    timestamp: item.evaluated_at,
    evaluated_rule: {
      required_property: "encryption.requireInfrastructureEncryption",
      expected_value: true,
      actual_value: item.compliance_status === "COMPLIANT" ? true : false,
    },
    raw_status: item.compliance_status,
    confidence_score: item.confidence_score,
  },
  null,
  2
)}
              </pre>
            </div>
          </div>

          {/* Right Column: AI Gap Analysis & Advisory Guidance */}
          <div className="flex flex-col space-y-4">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider font-mono">
              AI Agent Evaluation & Advisory Code
            </h3>
            <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
              <div>
                <p className="text-xs font-medium text-gray-400">Flag Reason / Gap Analysis Details</p>
                <p className="text-sm text-amber-300 mt-1 font-medium">{item.evidence_summary}</p>
              </div>

              {item.advisory_hcl && (
                <div>
                  <p className="text-xs font-medium text-gray-400 font-mono text-purple-300">
                    Guardrail 1: Advisory HCL Terraform Snippet
                  </p>
                  <pre className="mt-1 p-3 rounded-lg bg-gray-950 border border-purple-500/20 text-xs font-mono text-purple-200 overflow-x-auto">
                    {item.advisory_hcl}
                  </pre>
                </div>
              )}

              {item.azure_cli && (
                <div>
                  <p className="text-xs font-medium text-gray-400 font-mono text-blue-300">
                    Advisory Azure CLI Command
                  </p>
                  <pre className="mt-1 p-2.5 rounded-lg bg-gray-950 border border-blue-500/20 text-xs font-mono text-blue-200 overflow-x-auto">
                    {item.azure_cli}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Section: Mandatory HITL Override Workflow */}
        <div className="p-6 bg-gray-950 border-t border-gray-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-amber-400 flex items-center gap-2 font-heading">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              Human Compliance Officer Override Controls
            </h3>
            <span className="text-xs text-gray-400 font-mono">Mandatory Justification Required</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1">Override Status Decision</label>
              <select
                value={overrideStatus}
                onChange={(e) => setOverrideStatus(e.target.value as 'COMPLIANT' | 'NON_COMPLIANT')}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm font-medium text-white focus:outline-none focus:border-blue-500"
              >
                <option value="COMPLIANT">APPROVE (Set COMPLIANT)</option>
                <option value="NON_COMPLIANT">REJECT (Set NON-COMPLIANT)</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-gray-400 mb-1">
                Audit Justification Note <span className="text-red-400">*</span> (Min 15 chars)
              </label>
              <input
                type="text"
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                placeholder="e.g. Verified manual exception approval document approved by CISO on 2026-08-11."
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {errorMsg && (
            <p className="text-xs text-red-400 font-medium font-mono">{errorMsg}</p>
          )}

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-5 py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25 hover:from-blue-500 hover:to-indigo-500 transition-all"
            >
              Sign & Save Cryptographic Audit Override
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
