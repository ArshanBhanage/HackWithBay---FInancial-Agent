// import React from 'react'
import { AlertTriangle, CheckCircle2, ExternalLink, Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Violation, Severity, Status } from '@/types'
import { formatRelativeTime } from '@/lib/utils'

interface ViolationsTableProps {
  violations: Violation[]
  selectedViolation: Violation | null
  onSelectViolation: (violation: Violation) => void
  onAcknowledge: (id: string) => void
  onViewEvidence: (id: string) => void
}

function severityBadge(severity: Severity) {
  const styles: Record<Severity, string> = {
    HIGH: "bg-red-100 text-red-700 border-red-200",
    MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
    LOW: "bg-emerald-100 text-emerald-700 border-emerald-200",
  }
  return (
    <Badge className={`border ${styles[severity]} px-2 py-1 rounded-2xl`}>
      {severity}
    </Badge>
  )
}

function statusPill(status: Status) {
  const map: Record<Status, { icon: React.ReactNode; cls: string }> = {
    OPEN: { icon: <AlertTriangle className="w-4 h-4" />, cls: "bg-slate-100 text-slate-800" },
    ACK: { icon: <Bell className="w-4 h-4" />, cls: "bg-blue-100 text-blue-800" },
    RESOLVED: { icon: <CheckCircle2 className="w-4 h-4" />, cls: "bg-emerald-100 text-emerald-800" },
  }
  const it = map[status]
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-2xl text-xs ${it.cls}`}>
      {it.icon}
      {status}
    </span>
  )
}

export function ViolationsTable({ 
  violations, 
  selectedViolation, 
  onSelectViolation, 
  onAcknowledge, 
  onViewEvidence 
}: ViolationsTableProps) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Live Violations</CardTitle>
        <span className="text-sm text-muted-foreground">{violations.length} shown</span>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-2xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="text-left p-3">ID</th>
                <th className="text-left p-3">Severity</th>
                <th className="text-left p-3">Investor</th>
                <th className="text-left p-3">Rule</th>
                <th className="text-left p-3">Expected</th>
                <th className="text-left p-3">Actual</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Detected</th>
                <th className="text-left p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((violation) => (
                <tr 
                  key={violation.id} 
                  className={`border-t hover:bg-muted/50 cursor-pointer ${
                    selectedViolation?.id === violation.id ? 'bg-muted/30' : ''
                  }`}
                  onClick={() => onSelectViolation(violation)}
                >
                  <td className="p-3 font-mono text-xs text-muted-foreground">
                    {violation.id}
                  </td>
                  <td className="p-3">{severityBadge(violation.severity)}</td>
                  <td className="p-3">{violation.investor}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="rounded-2xl">
                        {violation.ruleType}
                      </Badge>
                      <span className="text-muted-foreground text-xs">
                        {violation.ruleId}
                      </span>
                    </div>
                  </td>
                  <td className="p-3">{violation.expected}</td>
                  <td className="p-3">{violation.actual}</td>
                  <td className="p-3">{statusPill(violation.status)}</td>
                  <td className="p-3 text-xs text-muted-foreground">
                    {formatRelativeTime(violation.detectedAt || violation.created_at || new Date().toISOString())}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="gap-1"
                        onClick={(e) => {
                          e.stopPropagation()
                          onViewEvidence(violation.id)
                        }}
                      >
                        <ExternalLink className="w-4 h-4" /> 
                        Evidence
                      </Button>
                      <Button 
                        size="sm" 
                        className="gap-1"
                        onClick={(e) => {
                          e.stopPropagation()
                          onAcknowledge(violation.id)
                        }}
                      >
                        <CheckCircle2 className="w-4 h-4" /> 
                        Ack
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
