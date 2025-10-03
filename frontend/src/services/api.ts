import axios from 'axios'
import { Violation, Contract, Policy, DashboardStats, TimeSeriesData } from '@/types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Health check
export const getHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

// Violations
export const getViolations = async (params?: {
  severity?: string
  status?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<Violation[]> => {
  try {
    const response = await api.get('/alerts', { params })
    const alerts = response.data.alerts || []
    // Map API response to frontend Violation interface
    return alerts.map((alert: any) => ({
      id: alert.alert_id,
      detectedAt: alert.created_at,
      investor: 'Unknown',
      contract: 'Unknown',
      ruleId: alert.alert_id,
      ruleType: 'compliance_check',
      expected: 'N/A',
      actual: 'N/A',
      severity: alert.severity,
      status: alert.status,
      evidence: {
        doc: 'Unknown',
        page: 1,
        text: alert.message
      }
    }))
  } catch (error) {
    console.error('Error fetching violations:', error)
    return []
  }
}

export const updateViolationStatus = async (id: string, status: string) => {
  const response = await api.patch(`/alerts/${id}`, { status })
  return response.data
}

export const acknowledgeViolation = async (id: string) => {
  const response = await api.post(`/alerts/${id}/acknowledge`)
  return response.data
}

// Contracts
export const getContracts = async (): Promise<Contract[]> => {
  try {
    const response = await api.get('/contracts')
    return response.data.contracts || []
  } catch (error) {
    console.error('Error fetching contracts:', error)
    return []
  }
}

export const uploadContract = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const detectDrift = async (contractId: string) => {
  const response = await api.post(`/contracts/${contractId}/detect-drift`)
  return response.data
}

// Policies
export const getPolicies = async (): Promise<Policy[]> => {
  try {
    const response = await api.get('/policies')
    return response.data.policies || []
  } catch (error) {
    console.error('Error fetching policies:', error)
    return []
  }
}

export const compilePolicy = async (policyData: any) => {
  const response = await api.post('/policies/compile', policyData)
  return response.data
}

// Dashboard
export const getDashboardStats = async (): Promise<DashboardStats> => {
  try {
    const response = await api.get('/dashboard/stats')
    return response.data
  } catch (error) {
    console.error('Error fetching dashboard stats:', error)
    return {
      totalViolations: 0,
      openViolations: 0,
      resolvedViolations: 0,
      highSeverityViolations: 0,
      contractsProcessed: 0,
      lastUpdated: new Date().toISOString()
    }
  }
}

export const getViolationsTimeSeries = async (days: number = 7): Promise<TimeSeriesData[]> => {
  try {
    const response = await api.get('/dashboard/violations-timeseries', {
      params: { days }
    })
    return response.data
  } catch (error) {
    console.error('Error fetching violations time series:', error)
    return []
  }
}

// Notifications
export const testNotifications = async () => {
  const response = await api.get('/notifications/test')
  return response.data
}

export const sendNotification = async (data: {
  type: 'slack' | 'crm' | 'dashboard'
  message: string
  severity: string
}) => {
  const response = await api.post('/notifications/send', data)
  return response.data
}

// WebSocket connection for real-time updates
export const createWebSocketConnection = (onMessage: (data: any) => void) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//localhost:8000/ws`
  
  const ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('WebSocket connected')
    onMessage({ type: 'connection', status: 'connected' })
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected')
    onMessage({ type: 'connection', status: 'disconnected' })
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    onMessage({ type: 'error', message: 'WebSocket connection error' })
  }
  
  return ws
}

export default api
