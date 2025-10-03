import React, { useState } from 'react'
import { Search, Bell, Download, FileCheck2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface HeaderProps {
  onSearch: (query: string) => void
  onExport: () => void
  onNotifications: () => void
  onRefresh: () => void
  isLive: boolean
  lastRefresh: Date
}

export function Header({ onSearch, onExport, onNotifications, onRefresh, isLive, lastRefresh }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(searchQuery)
  }

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <FileCheck2 className="w-6 h-6" />
          <span className="font-semibold">Financial Contract Drift Monitor</span>
        </div>
        
        <div className="ml-auto flex items-center gap-2">
          <form onSubmit={handleSearch} className="relative w-72">
            <Search className="w-4 h-4 absolute left-2 top-2.5 text-muted-foreground" />
            <Input 
              placeholder="Search violations, investors, rules..." 
              className="pl-8" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
          
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {isLive && (
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live</span>
              </div>
            )}
            <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
          </div>
          
          <Button variant="outline" size="sm" onClick={onRefresh} className="gap-1">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          
          <Button variant="outline" className="gap-2" onClick={onNotifications}>
            <Bell className="w-4 h-4" /> 
            Alerts
          </Button>
          
          <Button className="gap-2" onClick={onExport}>
            <Download className="w-4 h-4" /> 
            Export CSV
          </Button>
        </div>
      </div>
    </header>
  )
}