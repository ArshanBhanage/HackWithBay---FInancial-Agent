// import React from 'react'
import { PlayCircle, PauseCircle, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Select } from '@/components/ui/select'

interface ControlsProps {
  isLive: boolean
  onToggleLive: (live: boolean) => void
  severity: string
  onSeverityChange: (severity: string) => void
  onPause: () => void
  onResume: () => void
}

export function Controls({ 
  isLive, 
  onToggleLive, 
  severity, 
  onSeverityChange, 
  onPause, 
  onResume 
}: ControlsProps) {
  return (
    <div className="space-y-4">
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Stream Controls</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Switch checked={isLive} onChange={(e) => onToggleLive(e.target.checked)} />
            <span className="text-sm text-muted-foreground">
              {isLive ? "Live mode (SSE/WebSocket)" : "Paused"}
            </span>
          </div>
          <div className="flex gap-2">
            <Button 
              size="sm" 
              variant={isLive ? "secondary" : "default"} 
              className="gap-1"
              onClick={isLive ? onPause : onResume}
            >
              {isLive ? <PauseCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />} 
              {isLive ? "Pause" : "Resume"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Filter</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <Select value={severity} onChange={(e) => onSeverityChange(e.target.value)} className="w-48">
            <option value="ALL">All severities</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </Select>
        </CardContent>
      </Card>
    </div>
  )
}
