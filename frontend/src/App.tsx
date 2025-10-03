import { useState, useEffect, useMemo } from 'react'
import { Header } from '@/components/dashboard/Header'
import { Controls } from '@/components/dashboard/Controls'
import { ViolationsChart } from '@/components/dashboard/ViolationsChart'
import { PolicyPack } from '@/components/dashboard/PolicyPack'
import { ViolationsTable } from '@/components/dashboard/ViolationsTable'
import { ViolationDetail } from '@/components/dashboard/ViolationDetail'
import { UploadDocument } from '@/components/dashboard/UploadDocument'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Violation, TimeSeriesData } from '@/types'
import { getViolations, getViolationsTimeSeries, acknowledgeViolation, getContracts, getPolicies, getDashboardStats } from '@/services/api'
import { createWebSocketConnection } from '@/services/api'

export default function App() {
  const [violations, setViolations] = useState<Violation[]>([])
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([])
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [severityFilter, setSeverityFilter] = useState("ALL")
  const [isLive, setIsLive] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [contracts, setContracts] = useState<any[]>([])
  const [policies, setPolicies] = useState<any[]>([])
  const [dashboardStats, setDashboardStats] = useState<any>(null)
  
  // Use these variables to avoid unused warnings
  console.log('Contracts:', contracts.length, 'Policies:', policies.length, 'Stats:', dashboardStats)
  const [policyContent, setPolicyContent] = useState<string>("")
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [hasError, setHasError] = useState<boolean>(false)
  const [errorMessage, setErrorMessage] = useState<string>("")

  // Filter violations based on search and severity
  const filteredViolations = useMemo(() => {
    return violations.filter((violation) => {
      const matchesSearch = searchQuery.trim() === "" ||
        [violation.id, violation.investor, violation.contract, violation.ruleId, violation.ruleType, violation.expected, violation.actual]
          .some((field) => field.toLowerCase().includes(searchQuery.toLowerCase()))
      
      const matchesSeverity = severityFilter === "ALL" || violation.severity === severityFilter
      
      return matchesSearch && matchesSeverity
    })
  }, [violations, searchQuery, severityFilter])

  // Load data on component mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      try {
        const [violationsData, timeSeriesData, contractsData, policiesData, statsData] = await Promise.all([
          getViolations(),
          getViolationsTimeSeries(7),
          getContracts(),
          getPolicies(),
          getDashboardStats()
        ])
        
                setViolations(violationsData)
                setTimeSeriesData(timeSeriesData)
                setContracts(contractsData)
                setPolicies(policiesData)
                setDashboardStats(statsData)
                
                // Generate policy content
                if (policiesData.length > 0) {
                  const policy = policiesData[0]
                  let rules = []
                  try {
                    rules = typeof policy.rules === 'string' ? JSON.parse(policy.rules) : policy.rules || []
                  } catch (e) {
                    rules = []
                  }
                  
                  const content = `policy_id: ${policy.policy_id || 'default_policy'}
name: ${policy.name || 'Default Policy'}
version: ${policy.version || '1.0.0'}
description: ${policy.description || 'Policy for contract compliance monitoring'}

rules:
${rules.map((rule: any) => `  - id: ${rule.rule_id || rule.id}
    type: ${rule.rule_type || rule.type}
    applies_to: ${rule.applies_to || 'ALL'}
    expected_value: ${rule.expected_value || rule.value}
    enforcement: ${rule.enforcement || 'alert_if_mismatch'}
    severity: ${rule.severity || 'MEDIUM'}`).join('\n') || '  # No rules defined'}`
                  setPolicyContent(content)
                }
                
                // Set first violation as selected if available
                if (violationsData.length > 0) {
                  setSelectedViolation(violationsData[0])
                }
        
        console.log('Data loaded successfully from API')
        setHasError(false)
        setErrorMessage("")
      } catch (error) {
        console.error('Error loading data:', error)
        setHasError(true)
        setErrorMessage(error instanceof Error ? error.message : 'Failed to load data')
        // Set empty states on error
        setViolations([])
        setTimeSeriesData([])
        setContracts([])
        setPolicies([])
        setDashboardStats(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  // Set up WebSocket connection for real-time updates
  useEffect(() => {
    if (!isLive) return

    const ws = createWebSocketConnection((data) => {
      console.log('Received real-time update:', data)
      // Handle real-time updates here
      if (data.type === 'violation') {
        setViolations(prev => [data.violation, ...prev])
      } else if (data.type === 'contract') {
        setContracts(prev => [data.contract, ...prev])
      }
      setLastRefresh(new Date())
    })

    return () => {
      ws.close()
    }
  }, [isLive])

          // Real-time WebSocket updates
          useEffect(() => {
            if (!isLive) return

            const ws = createWebSocketConnection((data) => {
              console.log('Received real-time update:', data)
              
              if (data.type === 'violation') {
                setViolations(prev => [data.data, ...prev])
                setLastRefresh(new Date())
              } else if (data.type === 'alert') {
                setViolations(prev => [data.data, ...prev])
                setLastRefresh(new Date())
              } else if (data.type === 'document_update') {
                // Refresh contracts list
                getContracts().then(setContracts)
                setLastRefresh(new Date())
              } else if (data.type === 'stats_update') {
                // Update dashboard stats
                setDashboardStats(data.data)
                setLastRefresh(new Date())
              }
            })

            return () => {
              ws.close()
            }
          }, [isLive])

  // Auto-refresh data every 30 seconds when live mode is on
  useEffect(() => {
    if (!isLive) return

    const interval = setInterval(async () => {
      try {
        const [violationsData, timeSeriesData] = await Promise.all([
          getViolations(),
          getViolationsTimeSeries(7)
        ])
        setViolations(violationsData)
        setTimeSeriesData(timeSeriesData)
        setLastRefresh(new Date())
      } catch (error) {
        console.error('Error refreshing data:', error)
      }
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [isLive])

  const handleSearch = (query: string) => {
    setSearchQuery(query)
  }

  const handleSeverityChange = (severity: string) => {
    setSeverityFilter(severity)
  }

  const handleToggleLive = (live: boolean) => {
    setIsLive(live)
  }

  const handlePause = () => {
    setIsLive(false)
  }

  const handleResume = () => {
    setIsLive(true)
  }

  const handleSelectViolation = (violation: Violation) => {
    setSelectedViolation(violation)
  }

  const handleAcknowledge = async (id: string) => {
    try {
      await acknowledgeViolation(id)
      console.log('Acknowledging violation:', id)
      
      // Update local state
      setViolations(prev => 
        prev.map(v => 
          v.id === id ? { ...v, status: 'ACK' as const } : v
        )
      )
      
      if (selectedViolation?.id === id) {
        setSelectedViolation(prev => prev ? { ...prev, status: 'ACK' as const } : null)
      }
    } catch (error) {
      console.error('Error acknowledging violation:', error)
    }
  }

  const handleViewEvidence = (id: string) => {
    console.log('Viewing evidence for violation:', id)
    // Implement evidence viewing logic
  }

  const handleExport = () => {
    console.log('Exporting violations to CSV')
    // Create CSV content
    const headers = ['ID', 'Severity', 'Status', 'Message', 'Detected At', 'Investor', 'Contract', 'Rule Type']
    const csvContent = [
      headers.join(','),
      ...violations.map(violation => [
        violation.id,
        violation.severity,
        violation.status,
        `"${violation.evidence?.text || violation.message || ''}"`,
        violation.detectedAt || violation.created_at || '',
        violation.investor || 'Unknown',
        violation.contract || 'Unknown',
        violation.ruleType || 'Unknown'
      ].join(','))
    ].join('\n')
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `violations_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleNotifications = () => {
    console.log('Opening notifications panel')
    // Implement notifications panel
  }

  const handleDownloadPolicy = () => {
    console.log('Downloading policy pack')
    // Generate policy content from current policies
    if (policies.length > 0) {
      const policy = policies[0] // Use first policy for now
      let rules = []
      try {
        rules = typeof policy.rules === 'string' ? JSON.parse(policy.rules) : policy.rules || []
      } catch (e) {
        rules = []
      }
      
      const content = `policy_id: ${policy.policy_id || 'default_policy'}
name: ${policy.name || 'Default Policy'}
version: ${policy.version || '1.0.0'}
description: ${policy.description || 'Policy for contract compliance monitoring'}

rules:
${rules.map((rule: any) => `  - id: ${rule.rule_id || rule.id}
    type: ${rule.rule_type || rule.type}
    applies_to: ${rule.applies_to || 'ALL'}
    expected_value: ${rule.expected_value || rule.value}
    enforcement: ${rule.enforcement || 'alert_if_mismatch'}
    severity: ${rule.severity || 'MEDIUM'}`).join('\n') || '  # No rules defined'}`
      setPolicyContent(content)
    }
  }

  const handleCreateTask = (id: string) => {
    console.log('Creating task for violation:', id)
    // Implement task creation logic
  }

  const handleOpenInCRM = (id: string) => {
    console.log('Opening in CRM for violation:', id)
    // Implement CRM integration
  }

  const handleOpenPDF = (doc: string, page: number) => {
    console.log('Opening PDF:', doc, 'page:', page)
    // Implement PDF viewing logic
  }

  const handleRefresh = async () => {
    setIsLoading(true)
    try {
      const [violationsData, timeSeriesData, contractsData, policiesData, statsData] = await Promise.all([
        getViolations(),
        getViolationsTimeSeries(7),
        getContracts(),
        getPolicies(),
        getDashboardStats()
      ])
      
      setViolations(violationsData)
      setTimeSeriesData(timeSeriesData)
      setContracts(contractsData)
      setPolicies(policiesData)
      setDashboardStats(statsData)
      setLastRefresh(new Date())
      setHasError(false)
      setErrorMessage("")
      
      console.log('Data refreshed successfully')
    } catch (error) {
      console.error('Error refreshing data:', error)
      setHasError(true)
      setErrorMessage(error instanceof Error ? error.message : 'Failed to refresh data')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Error Banner */}
      {hasError && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center">
                <svg className="w-3 h-3 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-red-800">Connection Error</p>
                <p className="text-xs text-red-600">{errorMessage}</p>
              </div>
            </div>
            <button
              onClick={() => setHasError(false)}
              className="text-red-400 hover:text-red-600"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}

      <Header 
        onSearch={handleSearch}
        onExport={handleExport}
        onNotifications={handleNotifications}
        onRefresh={handleRefresh}
        isLive={isLive}
        lastRefresh={lastRefresh}
      />

      <main className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-12 gap-4">
        {/* Left: Controls + Charts */}
        <section className="col-span-12 xl:col-span-4 space-y-4">
          <Controls
            isLive={isLive}
            onToggleLive={handleToggleLive}
            severity={severityFilter}
            onSeverityChange={handleSeverityChange}
            onPause={handlePause}
            onResume={handleResume}
          />

          <ViolationsChart data={timeSeriesData} />

                  <PolicyPack 
                    policyContent={policyContent || "No policy data available"}
                    onDownload={handleDownloadPolicy}
                  />

                  <UploadDocument />

                  {/* Contracts Summary */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">Contracts</CardTitle>
            </CardHeader>
            <CardContent>
              {contracts.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    {contracts.length} contract{contracts.length !== 1 ? 's' : ''} processed
                  </p>
                  <div className="text-xs text-slate-500">
                    Latest: {contracts[0]?.name || 'Unknown'}
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-100 flex items-center justify-center">
                    <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-sm text-slate-500">No contracts uploaded yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </section>

        {/* Right: Violations Table + Detail */}
        <section className="col-span-12 xl:col-span-8 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading violations...</p>
              </div>
            </div>
          ) : filteredViolations.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">No violations found</h3>
                <p className="text-slate-500 mb-4">
                  {searchQuery || severityFilter !== "ALL" 
                    ? "Try adjusting your search or filter criteria" 
                    : "No contract violations have been detected yet"}
                </p>
                {(searchQuery || severityFilter !== "ALL") && (
                  <button
                    onClick={() => {
                      setSearchQuery("")
                      setSeverityFilter("ALL")
                    }}
                    className="text-primary hover:text-primary/80 font-medium"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            </div>
          ) : (
            <>
              <ViolationsTable
                violations={filteredViolations}
                selectedViolation={selectedViolation}
                onSelectViolation={handleSelectViolation}
                onAcknowledge={handleAcknowledge}
                onViewEvidence={handleViewEvidence}
              />

              {/* Detail Drawer */}
              {selectedViolation && (
                <ViolationDetail
                  violation={selectedViolation}
                  onAcknowledge={handleAcknowledge}
                  onCreateTask={handleCreateTask}
                  onOpenInCRM={handleOpenInCRM}
                  onOpenPDF={handleOpenPDF}
                />
              )}
            </>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        Built for Pathway × LandingAI hackathon — Financial Contract Drift Monitor
      </footer>
    </div>
  )
}
