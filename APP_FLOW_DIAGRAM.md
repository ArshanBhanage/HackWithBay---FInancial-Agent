# Financial Contract Drift Monitor - Application Flow

## 🏗️ **System Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Financial Contract Drift Monitor              │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript)     │  Backend (FastAPI + Python) │
│  ┌─────────────────────────────┐   │  ┌─────────────────────────┐ │
│  │ • Dashboard UI              │   │  │ • API Endpoints         │ │
│  │ • Real-time Updates         │   │  │ • Document Processing   │ │
│  │ • Demo Data Generation      │   │  │ • Drift Detection       │ │
│  │ • Violation Management      │   │  │ • Policy Compilation    │ │
│  └─────────────────────────────┘   │  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 **Application Startup Flow**

### **1. Backend Startup (`main.py`)**
```
1. Load Configuration (.env file)
   ├── API Keys (LandingAI, Pathway)
   ├── Database URL
   ├── Webhook Secrets
   └── Service Settings

2. Initialize Services
   ├── PathwayService (Document ingestion)
   ├── LandingAIService (Document extraction)
   ├── DriftDetector (Change detection)
   ├── PolicyCompiler (Rule compilation)
   ├── ValidationEngine (Compliance checking)
   └── NotificationService (Alerts)

3. Start FastAPI Server
   ├── CORS Middleware
   ├── Static File Serving
   └── API Routes Registration
```

### **2. Frontend Startup (`npm run dev`)**
```
1. Vite Development Server
   ├── React App Compilation
   ├── TypeScript Type Checking
   ├── Tailwind CSS Processing
   └── Hot Module Replacement

2. App Component Mount
   ├── State Initialization
   ├── API Service Setup
   ├── Demo Data Generation
   └── Real-time Simulation Start
```

## 🔄 **Data Flow Architecture**

### **Primary Data Flow**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Frontend  │◄──►│   Backend    │◄──►│   Services  │
│             │    │              │    │             │
│ • React UI  │    │ • FastAPI    │    │ • Pathway   │
│ • Demo Data │    │ • Endpoints  │    │ • LandingAI │
│ • Real-time │    │ • Processing │    │ • Detection │
└─────────────┘    └──────────────┘    └─────────────┘
```

### **API Request Flow**
```
1. Frontend Component
   ├── User Interaction (Search, Filter, etc.)
   ├── State Update Request
   └── API Service Call

2. API Service (`services/api.ts`)
   ├── HTTP Request to Backend
   ├── Error Handling
   ├── Demo Data Fallback (if backend empty)
   └── Response Processing

3. Backend Endpoint (`app/api/main.py`)
   ├── Request Validation
   ├── Service Integration
   ├── Data Processing
   └── Response Generation

4. Frontend State Update
   ├── Data Integration
   ├── UI Re-render
   └── User Feedback
```

## 📊 **Demo Data Generation Flow**

### **Faker.js Integration**
```
┌─────────────────────────────────────────────────────────────┐
│                    Demo Data Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. API Call Made                                           │
│     ├── Backend Returns Empty Data                          │
│     └── Frontend Detects Empty Response                     │
│                                                             │
│  2. Demo Data Generator Triggered                           │
│     ├── `generateViolations(8)`                             │
│     ├── `generateContracts()`                               │
│     ├── `generatePolicies()`                                │
│     ├── `generateDashboardStats()`                          │
│     └── `generateTimeSeriesData(7)`                         │
│                                                             │
│  3. Realistic Data Creation                                 │
│     ├── Seeded Randomness (faker.seed(12345))              │
│     ├── Context-Appropriate Values                          │
│     ├── Proper TypeScript Interfaces                        │
│     └── Financial Domain Logic                              │
│                                                             │
│  4. Frontend State Update                                   │
│     ├── Component Re-render                                 │
│     ├── Chart Updates                                       │
│     └── User Interface Refresh                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Real-time Simulation Flow**
```
┌─────────────────────────────────────────────────────────────┐
│                Real-time Demo Stream                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every 15 Seconds (when live mode is ON):                  │
│                                                             │
│  1. New Violation Generation                                │
│     ├── `makeFakeViolation(violations.length)`             │
│     ├── Realistic Financial Context                         │
│     ├── Proper Severity & Status                            │
│     └── Evidence with Document References                   │
│                                                             │
│  2. State Updates                                           │
│     ├── Add to Violations List                              │
│     ├── Update Time Series Chart                            │
│     ├── Refresh Dashboard Stats                             │
│     └── Update Last Refresh Time                            │
│                                                             │
│  3. UI Updates                                              │
│     ├── New Violation Appears in Table                      │
│     ├── Chart Bars Update                                   │
│     ├── Live Status Indicator                               │
│     └── Console Logging                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 **User Interaction Flow**

### **Dashboard Navigation**
```
┌─────────────────────────────────────────────────────────────┐
│                    User Experience Flow                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Page Load                                               │
│     ├── App.tsx Component Mounts                            │
│     ├── Initial Data Loading                                │
│     ├── Demo Data Generation                                │
│     └── Real-time Stream Start                              │
│                                                             │
│  2. Dashboard Display                                       │
│     ├── Header with Search & Controls                       │
│     ├── Left Panel: Controls, Charts, Policy Pack          │
│     ├── Right Panel: Violations Table & Detail View        │
│     └── Live Status Indicators                              │
│                                                             │
│  3. User Interactions                                       │
│     ├── Search Violations                                   │
│     ├── Filter by Severity                                  │
│     ├── Toggle Live Mode                                    │
│     ├── Select Violation for Details                        │
│     ├── Acknowledge Violations                              │
│     └── Export Data                                         │
│                                                             │
│  4. Real-time Updates                                       │
│     ├── New Violations Every 15s                            │
│     ├── Chart Data Updates                                  │
│     ├── Dashboard Stats Refresh                             │
│     └── Live Status Indicators                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Service Integration Flow**

### **Backend Services**
```
┌─────────────────────────────────────────────────────────────┐
│                    Service Integration                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PathwayService (Document Ingestion)                    │
│     ├── File System Monitoring                             │
│     ├── Document Stream Processing                          │
│     ├── Metadata Extraction                                │
│     └── Real-time Updates                                  │
│                                                             │
│  2. LandingAIService (Document Extraction)                 │
│     ├── PDF Text Extraction                                │
│     ├── Structured Data Parsing                            │
│     ├── Field Recognition                                  │
│     └── Confidence Scoring                                 │
│                                                             │
│  3. DriftDetector (Change Detection)                       │
│     ├── Version Comparison                                 │
│     ├── Semantic Diff Analysis                             │
│     ├── Risk Assessment                                    │
│     └── Violation Generation                               │
│                                                             │
│  4. PolicyCompiler (Rule Compilation)                      │
│     ├── Policy Rule Parsing                                │
│     ├── Constraint Generation                              │
│     ├── SQL/DSL Compilation                                │
│     └── Enforcement Logic                                  │
│                                                             │
│  5. ValidationEngine (Compliance Checking)                 │
│     ├── Rule Application                                   │
│     ├── Violation Detection                                │
│     ├── Severity Assessment                                │
│     └── Alert Generation                                   │
│                                                             │
│  6. NotificationService (Alert Management)                 │
│     ├── Alert Creation                                     │
│     ├── Severity Routing                                   │
│     ├── Multi-channel Delivery                             │
│     └── Escalation Logic                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 **Document Processing Flow**

### **Document Upload & Processing**
```
┌─────────────────────────────────────────────────────────────┐
│                Document Processing Pipeline                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Document Upload                                         │
│     ├── User selects file (PDF, CSV, etc.)                 │
│     ├── Frontend validation                                │
│     ├── FormData preparation                               │
│     └── POST /upload endpoint                              │
│                                                             │
│  2. Backend Processing                                      │
│     ├── File validation & storage                          │
│     ├── PathwayService integration                         │
│     ├── LandingAIService extraction                        │
│     └── Version tracking                                   │
│                                                             │
│  3. Data Extraction                                         │
│     ├── OCR processing (PDFs)                              │
│     ├── Structured data parsing                            │
│     ├── Field mapping & validation                         │
│     └── Confidence scoring                                 │
│                                                             │
│  4. Drift Detection                                         │
│     ├── Previous version comparison                        │
│     ├── Semantic difference analysis                       │
│     ├── Risk impact assessment                             │
│     └── Violation generation                               │
│                                                             │
│  5. Policy Compliance                                       │
│     ├── Rule application                                   │
│     ├── Constraint checking                                │
│     ├── Violation detection                                │
│     └── Alert generation                                   │
│                                                             │
│  6. Real-time Updates                                       │
│     ├── Frontend notification                              │
│     ├── Dashboard refresh                                  │
│     ├── Chart updates                                      │
│     └── User alerts                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 **Error Handling & Fallback Flow**

### **Resilient Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    Error Handling Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. API Request Failure                                     │
│     ├── Network error detection                            │
│     ├── Timeout handling                                   │
│     ├── HTTP status code checking                          │
│     └── Fallback to demo data                              │
│                                                             │
│  2. Backend Service Failure                                 │
│     ├── Service initialization error                       │
│     ├── Mock mode activation                               │
│     ├── Graceful degradation                               │
│     └── User notification                                  │
│                                                             │
│  3. Frontend Error Recovery                                 │
│     ├── JavaScript error boundaries                        │
│     ├── Component error handling                           │
│     ├── State recovery                                     │
│     └── User feedback                                      │
│                                                             │
│  4. Data Validation Errors                                  │
│     ├── TypeScript type checking                           │
│     ├── Runtime validation                                 │
│     ├── Default value assignment                           │
│     └── Error logging                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 **Current System Status**

### **✅ Working Components**
- **Frontend**: React dashboard with demo data
- **Backend**: FastAPI server with endpoints
- **Demo Data**: Faker.js integration with real-time updates
- **API Integration**: Smart fallback logic
- **Error Handling**: Graceful degradation
- **Real-time Simulation**: 15-second violation generation

### **⚠️ Current Limitations**
- **LandingAI**: Mock mode (API key format issue)
- **Pathway**: Mock mode (ColumnReference error)
- **Database**: In-memory storage only
- **WebSocket**: Mock implementation
- **Document Processing**: Limited to demo documents

### **🚀 Demo Experience**
- **8 realistic violations** with proper severity levels
- **Live data stream** adding new violations every 15 seconds
- **Dynamic charts** updating in real-time
- **Professional dashboard** with realistic metrics
- **Smart API integration** with demo data fallback
- **Document access** for evidence viewing
- **Seeded randomness** for consistent demo runs

## 🎉 **Result**

The Financial Contract Drift Monitor provides a **complete, professional demo experience** that simulates a live financial contract monitoring system with realistic data, real-time updates, and robust error handling. Perfect for demonstrations, testing, and development!
