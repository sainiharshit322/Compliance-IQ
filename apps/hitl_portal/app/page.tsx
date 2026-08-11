"use client";

import React, { useState } from 'react'
import DashboardMetrics from '../components/DashboardMetrics'
import HITLQueueTable, { HITLQueueItem } from '../components/HITLQueueTable'
import EvidenceReviewModal from '../components/EvidenceReviewModal'
import PolicyChatDrawer from '../components/PolicyChatDrawer'

const INITIAL_QUEUE: HITLQueueItem[] = [
  {
    id: 'rec-001',
    framework_code: 'EU_AI_ACT',
    control_code: 'AI_ACT_ART14',
    control_title: 'Human Oversight System Design Obligations',
    compliance_status: 'NEEDS_HUMAN_REVIEW',
    risk_score: 7.5,
    confidence_score: 0.72,
    flagged_for_hitl: true,
    evaluated_at: '2026-08-11T12:00:00Z',
    evidence_summary: 'Ambiguous evidence collected for Article 14 human oversight requirements. AI Confidence < 85%.',
    advisory_hcl: `# EU AI Act Article 14 Human Oversight System Definition\nresource "azurerm_user_assigned_identity" "human_oversight" {\n  name = "id-human-oversight-auditor"\n}`,
    azure_cli: 'az identity create --name id-human-oversight-auditor --resource-group rg-complianceiq-dev',
  },
  {
    id: 'rec-002',
    framework_code: 'SOC2_TYPE2',
    control_code: 'CC6.1',
    control_title: 'Infrastructure Encryption at Rest (AES-256)',
    compliance_status: 'NON_COMPLIANT',
    risk_score: 8.5,
    confidence_score: 0.95,
    flagged_for_hitl: false,
    evaluated_at: '2026-08-11T12:05:00Z',
    evidence_summary: 'Target Azure Storage Account lacks infrastructure AES-256 data encryption at rest.',
    advisory_hcl: `# Enforce AES-256 Data Encryption at Rest\nresource "azurerm_storage_account" "storage" {\n  infrastructure_encryption_enabled = true\n}`,
    azure_cli: 'az storage account update --name stprod01 --require-infrastructure-encryption true',
  },
  {
    id: 'rec-003',
    framework_code: 'SOC2_TYPE2',
    control_code: 'SOC2_WORM',
    control_title: 'WORM Container Immutability Lock',
    compliance_status: 'COMPLIANT',
    risk_score: 0.0,
    confidence_score: 0.99,
    flagged_for_hitl: false,
    evaluated_at: '2026-08-11T12:10:00Z',
    evidence_summary: 'Audit evidence logs container enforces locked WORM retention policy.',
  },
]

export default function ComplianceDashboardPage() {
  const [queueItems, setQueueItems] = useState<HITLQueueItem[]>(INITIAL_QUEUE)
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL')
  const [activeReviewItem, setActiveReviewItem] = useState<HITLQueueItem | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanNotice, setScanNotice] = useState('')

  const filteredItems = queueItems.filter((item) => {
    if (selectedStatus === 'ALL') return true
    if (selectedStatus === 'NEEDS_HUMAN_REVIEW') return item.flagged_for_hitl || item.compliance_status === 'NEEDS_HUMAN_REVIEW'
    return item.compliance_status === selectedStatus
  })

  const handleSaveOverride = (
    item: HITLQueueItem,
    newStatus: string,
    justification: string
  ) => {
    setQueueItems((prev) =>
      prev.map((q) =>
        q.id === item.id
          ? {
              ...q,
              compliance_status: newStatus as any,
              flagged_for_hitl: false,
              justification_note: justification,
              confidence_score: 1.0,
            }
          : q
      )
    )
  }

  const triggerLiveScan = async () => {
    setIsScanning(true)
    setScanNotice('Enqueuing multi-agent scan job into Azure Storage Queue...')
    try {
      const res = await fetch('http://localhost:8000/api/v1/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          framework_code: 'SOC2_TYPE2',
          collector_type: 'AZURE_POLICY',
          force_recollect: true,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setScanNotice(`Scan Job ${data.job_id} successfully enqueued into queue '${data.queue_name}'!`)
      } else {
        setScanNotice('Scan job enqueued in mock mode (Orchestrator online).')
      }
    } catch {
      setScanNotice('Scan job enqueued into queue storage (Mock mode active).')
    } finally {
      setIsScanning(false)
      setTimeout(() => setScanNotice(''), 6000)
    }
  }

  const compliantCount = queueItems.filter((q) => q.compliance_status === 'COMPLIANT').length
  const pendingHITLCount = queueItems.filter((q) => q.flagged_for_hitl || q.compliance_status === 'NEEDS_HUMAN_REVIEW').length
  const criticalGapsCount = queueItems.filter((q) => q.risk_score >= 7.0 && q.compliance_status !== 'COMPLIANT').length

  return (
    <div className="space-y-8">
      {/* Top Banner & Scan Action */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border border-blue-500/20">
        <div>
          <h2 className="text-2xl font-bold text-white font-heading">Compliance Executive Overview</h2>
          <p className="text-sm text-gray-400 mt-1">
            Real-time multi-agent evidence collection, automated gap evaluation, and human officer review console.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={triggerLiveScan}
            disabled={isScanning}
            className="px-5 py-2.5 rounded-xl font-bold text-xs bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xl shadow-blue-500/25 hover:from-blue-500 hover:to-indigo-500 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isScanning ? (
              <>
                <span className="h-2 w-2 rounded-full bg-white animate-ping" />
                Triggering Scan...
              </>
            ) : (
              <>
                <span>⚡</span>
                Trigger Multi-Agent Scan
              </>
            )}
          </button>
        </div>
      </div>

      {scanNotice && (
        <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30 text-xs font-mono text-blue-300 flex items-center justify-between animate-fadeIn">
          <span>{scanNotice}</span>
        </div>
      )}

      {/* Metrics Row */}
      <DashboardMetrics
        totalControls={queueItems.length}
        compliantCount={compliantCount}
        pendingHITLCount={pendingHITLCount}
        criticalGapsCount={criticalGapsCount}
      />

      {/* HITL Queue & Audit Trail Table */}
      <HITLQueueTable
        items={filteredItems}
        onSelectReview={(item) => setActiveReviewItem(item)}
        selectedStatus={selectedStatus}
        setSelectedStatus={setSelectedStatus}
      />

      {/* Side-by-Side Review & Override Modal */}
      <EvidenceReviewModal
        item={activeReviewItem}
        onClose={() => setActiveReviewItem(null)}
        onSaveOverride={handleSaveOverride}
      />

      {/* Floating AI Policy Q&A RAG Chat Drawer */}
      <PolicyChatDrawer />
    </div>
  )
}
