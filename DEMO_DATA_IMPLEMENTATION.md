# Demo Data Implementation with Faker.js ✅

## 🎯 **Overview**

Successfully implemented dynamic demo data generation using `@faker-js/faker` to replace static mock data with realistic, randomly generated content that simulates a live financial contract monitoring system.

## 📦 **Installation & Setup**

### **1. Installed Faker.js**
```bash
cd frontend
npm install @faker-js/faker
```

### **2. Created Demo Data Generator**
**File**: `/frontend/src/utils/demoData.ts`

**Key Features:**
- ✅ **Seeded random data** for consistent demo experience
- ✅ **Realistic financial violations** with proper severity levels
- ✅ **Dynamic time series data** for charts
- ✅ **Contract metadata** with processing status
- ✅ **Policy rules** with enforcement logic

## 🔧 **Demo Data Functions**

### **1. Violations Generator**
```typescript
export function makeFakeViolation(id: number): Violation {
  // Generates realistic violations with:
  // - Context-appropriate expected/actual values
  // - Proper severity levels (HIGH/MEDIUM/LOW)
  // - Status tracking (OPEN/ACK/RESOLVED)
  // - Evidence with document references
}
```

### **2. Time Series Data**
```typescript
export function generateTimeSeriesData(days: number = 7): TimeSeriesData[] {
  // Creates realistic violation counts over time
  // Updates dynamically in real-time simulation
}
```

### **3. Dashboard Statistics**
```typescript
export function generateDashboardStats() {
  // Generates realistic metrics:
  // - Total violations (15-45)
  // - Open violations (5-15)
  // - High severity violations (2-8)
  // - Contracts processed (25-75)
}
```

### **4. Contract Data**
```typescript
export function generateContracts() {
  // Creates contract objects with:
  // - Proper TypeScript interface compliance
  // - Processing status tracking
  // - Extracted fields with confidence scores
  // - Investor and document type information
}
```

### **5. Policy Rules**
```typescript
export function generatePolicies() {
  // Generates policy objects with:
  // - Rule definitions and enforcement logic
  // - Severity levels and descriptions
  // - Field mappings and operators
}
```

## 🚀 **Real-Time Simulation**

### **Live Data Stream**
**File**: `/frontend/src/App.tsx`

```typescript
// Simulate real-time demo data stream
useEffect(() => {
  if (!isLive || violations.length === 0) return

  const timer = setInterval(() => {
    // Add new violation every 15 seconds
    const newViolation = makeFakeViolation(violations.length)
    setViolations(prev => [newViolation, ...prev])
    
    // Update time series data
    setTimeSeriesData(prev => {
      const today = new Date().toLocaleDateString('en-US', { weekday: 'short' })
      return prev.map(item => 
        item.day === today 
          ? { ...item, count: item.count + 1 }
          : item
      )
    })
  }, 15000) // Every 15 seconds

  return () => clearInterval(timer)
}, [isLive, violations.length])
```

## 📁 **Demo Documents**

### **Created Documents Directory**
**Location**: `/documents/`

**Files Added:**
- ✅ `LPA_v3.pdf` - Limited Partnership Agreement
- ✅ `SideLetter_InstitutionA.pdf` - Institution A side letter
- ✅ `SideLetter_FoundationB.pdf` - Foundation B side letter  
- ✅ `fees.csv` - Fee data with intentional violations
- ✅ `reports.csv` - Reporting deadlines with mismatches

### **Backend Document Endpoints**
**File**: `/app/api/main.py`

```python
@app.get("/demo/documents")
async def list_demo_documents():
    """List available demo documents."""
    # Returns document metadata

@app.get("/documents/{filename}")
async def get_document(filename: str):
    """Serve demo documents."""
    # Serves actual document files
```

## 🔄 **API Integration**

### **Smart Fallback Logic**
**File**: `/frontend/src/services/api.ts`

```typescript
export const getViolations = async (): Promise<Violation[]> => {
  try {
    const response = await api.get('/alerts', { params })
    const violations = response.data.alerts || []
    
    // If no violations from API, return demo data
    if (violations.length === 0) {
      return generateViolations(8)
    }
    
    return violations
  } catch (error) {
    // Return demo data on error
    return generateViolations(8)
  }
}
```

**Applied to all endpoints:**
- ✅ `getViolations()` - Returns 8 fake violations
- ✅ `getContracts()` - Returns 5 fake contracts
- ✅ `getPolicies()` - Returns 1 fake policy
- ✅ `getDashboardStats()` - Returns realistic metrics
- ✅ `getViolationsTimeSeries()` - Returns 7-day chart data

## 🎨 **User Experience**

### **Before Demo Data:**
- ❌ Empty screens with "No data available"
- ❌ Static hardcoded values
- ❌ No sense of live monitoring
- ❌ Boring demo experience

### **After Demo Data:**
- ✅ **Rich, realistic data** - Violations with proper context
- ✅ **Live updates** - New violations every 15 seconds
- ✅ **Dynamic charts** - Time series that updates in real-time
- ✅ **Professional metrics** - Dashboard stats that feel real
- ✅ **Seeded randomness** - Consistent demo experience
- ✅ **Smart fallbacks** - Works even if backend is down

## 🎯 **Demo Scenarios**

### **1. Fee Rate Violations**
- **Expected**: 1.75% management fee
- **Actual**: 2.00% management fee
- **Severity**: HIGH
- **Evidence**: Document page reference

### **2. Reporting Deadline Violations**
- **Expected**: ≤ 5 business days
- **Actual**: 7 business days
- **Severity**: MEDIUM
- **Evidence**: Contract clause text

### **3. Prohibited Sector Allocations**
- **Expected**: No allocation to SIC:7372
- **Actual**: Trade allocated to SIC:7372
- **Severity**: HIGH
- **Evidence**: Trade confirmation

### **4. MFN Notice Requirements**
- **Expected**: Notify if ≥ 10 bps more favorable
- **Actual**: Notice not sent
- **Severity**: MEDIUM
- **Evidence**: Side letter clause

## 🚀 **Result**

The Financial Contract Drift Monitor now provides a **professional, engaging demo experience** with:

- **8 realistic violations** with proper severity and status
- **Live data stream** that adds new violations every 15 seconds
- **Dynamic charts** that update in real-time
- **Professional dashboard** with realistic metrics
- **Smart API integration** that falls back to demo data
- **Document access** for evidence viewing
- **Seeded randomness** for consistent demo runs

**Perfect for demos, presentations, and testing!** 🎉
