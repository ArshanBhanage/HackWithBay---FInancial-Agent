// import React from 'react'
import { FileText, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface PolicyPackProps {
  policyContent: string
  onDownload: () => void
}

export function PolicyPack({ policyContent, onDownload }: PolicyPackProps) {
  const hasContent = policyContent && policyContent.trim() !== "" && policyContent !== "No policy data available"
  
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Policy Pack</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground space-y-2">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4" />
          <span>policy_pack.yaml</span>
        </div>
        
        {hasContent ? (
          <div className="rounded-xl bg-muted p-3 border text-xs overflow-auto max-h-56">
            <pre className="whitespace-pre-wrap font-mono">
              {policyContent}
            </pre>
          </div>
        ) : (
          <div className="rounded-xl bg-slate-50 p-6 border text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-100 flex items-center justify-center">
              <FileText className="w-6 h-6 text-slate-400" />
            </div>
            <p className="text-sm text-slate-500 mb-2">No policy data available</p>
            <p className="text-xs text-slate-400">Upload contracts to generate policy rules</p>
          </div>
        )}
        
        <Button 
          variant="outline" 
          className="gap-2" 
          onClick={onDownload}
          disabled={!hasContent}
        >
          <Download className="w-4 h-4" /> 
          Download
        </Button>
      </CardContent>
    </Card>
  )
}
