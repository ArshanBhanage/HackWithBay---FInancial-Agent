// import React from 'react'
import { Diff, ExternalLink, CheckCircle2, Bell, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Violation } from '@/types'
import { formatDate } from '@/lib/utils'

interface ViolationDetailProps {
  violation: Violation
  onAcknowledge: (id: string) => void
  onCreateTask: (id: string) => void
  onOpenInCRM: (id: string) => void
  onOpenPDF: (doc: string, page: number) => void
}

export function ViolationDetail({ 
  violation, 
  onAcknowledge, 
  onCreateTask, 
  onOpenInCRM, 
  onOpenPDF 
}: ViolationDetailProps) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2 flex items-center justify-between">
        <CardTitle className="text-lg flex items-center gap-2">
          <Diff className="w-5 h-5" /> 
          Details — {violation.id}
        </CardTitle>
        <div className="text-sm text-muted-foreground flex items-center gap-4">
          <span>Detected: {formatDate(violation.detectedAt || violation.created_at || new Date().toISOString())}</span>
          {violation.evidence?.doc && (
            <span>Doc: {violation.evidence.doc} p.{violation.evidence.page || 1}</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-12 gap-4">
          {/* Evidence Panel */}
          <div className="col-span-12 lg:col-span-6 space-y-3">
            <div className="rounded-2xl border bg-white overflow-hidden">
              <div className="px-3 py-2 bg-muted border-b flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  Evidence {violation.evidence?.page ? `(page ${violation.evidence.page})` : ''}
                </span>
                {violation.evidence?.doc && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="gap-1 text-xs"
                    onClick={() => onOpenPDF(violation.evidence.doc, violation.evidence.page || 1)}
                  >
                    <ExternalLink className="w-4 h-4" /> 
                    Open PDF
                  </Button>
                )}
              </div>
              <div className="p-4">
                <div className="h-48 rounded-xl bg-muted border flex items-center justify-center text-muted-foreground text-xs">
                  PDF page preview here
                </div>
                <div className="mt-3 text-sm">
                  <span className="font-medium">Clause snippet:</span>
                  <p className="mt-1 rounded-xl bg-muted border p-3 text-muted-foreground">
                    {violation.evidence?.text || violation.message || 'No evidence text available'}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border bg-white overflow-hidden">
              <div className="px-3 py-2 bg-muted border-b text-xs text-muted-foreground">
                Policy Rule
              </div>
              <div className="p-3 text-xs font-mono">
                <pre className="whitespace-pre-wrap">
{`id: ${violation.ruleId || violation.id}
type: ${violation.ruleType || 'unknown'}
expected: ${violation.expected || 'N/A'}
enforcement: block_if_mismatch`}
                </pre>
              </div>
            </div>
          </div>

          {/* Diff + Actions */}
          <div className="col-span-12 lg:col-span-6 space-y-3">
            <Tabs defaultValue="delta">
              <TabsList className="grid grid-cols-2 w-full">
                <TabsTrigger value="delta">Semantic Diff</TabsTrigger>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
              </TabsList>
              
              <TabsContent value="delta" className="mt-3">
                <div className="rounded-2xl border p-3 bg-white">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    <ChevronLeft className="w-4 h-4" /> 
                    Expected
                  </div>
                  <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-sm">
                    {violation.expected || "No expected value defined"}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mt-3 mb-2">
                    <ChevronRight className="w-4 h-4" /> 
                    Actual
                  </div>
                  <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm">
                    {violation.actual || "No actual value detected"}
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="timeline" className="mt-3">
                <ol className="relative border-s border-border pl-6 space-y-4">
                  <li>
                    <div className="absolute -left-2 top-0 w-4 h-4 rounded-full bg-emerald-500" />
                    <p className="text-sm">{new Date().toISOString().split('T')[0]} — Policy compiled from docs (v1)</p>
                  </li>
                  <li>
                    <div className="absolute -left-2 top-0 w-4 h-4 rounded-full bg-amber-500" />
                    <p className="text-sm">{violation.detectedAt ? new Date(violation.detectedAt).toISOString().split('T')[0] : new Date().toISOString().split('T')[0]} — Contract processed</p>
                  </li>
                  <li>
                    <div className="absolute -left-2 top-0 w-4 h-4 rounded-full bg-red-500" />
                    <p className="text-sm">{violation.detectedAt ? new Date(violation.detectedAt).toISOString().replace('T', ' ').split('.')[0] : new Date().toISOString().replace('T', ' ').split('.')[0]} — Violation detected</p>
                  </li>
                </ol>
              </TabsContent>
            </Tabs>

            <div className="rounded-2xl border bg-white p-3 flex flex-wrap items-center gap-2">
              <Button 
                className="gap-2" 
                variant="default"
                onClick={() => onAcknowledge(violation.id)}
              >
                <CheckCircle2 className="w-4 h-4" /> 
                Acknowledge
              </Button>
              <Button 
                className="gap-2" 
                variant="outline"
                onClick={() => onCreateTask(violation.id)}
              >
                <Bell className="w-4 h-4" /> 
                Create Task
              </Button>
              <Button 
                className="gap-2" 
                variant="outline"
                onClick={() => onOpenInCRM(violation.id)}
              >
                <ExternalLink className="w-4 h-4" /> 
                Open in CRM
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
