# Document Upload Guide

## 🚀 **Where to Upload Documents**

You can upload documents in **3 different ways**:

### **1. Frontend Dashboard (Recommended)**
- **URL**: http://localhost:3000
- **Location**: Left sidebar → "Upload Documents" component
- **Features**:
  - Drag and drop interface
  - File validation
  - Progress tracking
  - Real-time status updates
  - Multiple file upload

### **2. Backend API Endpoint**
- **URL**: http://localhost:8000/upload
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Usage**: 
  ```bash
  curl -X POST -F "file=@your_document.pdf" http://localhost:8000/upload
  ```

### **3. Backend Dashboard**
- **URL**: http://localhost:8000
- **Location**: Root page with upload area
- **Features**: Basic HTML upload interface

## 📁 **Supported File Types**

- **PDF**: `.pdf` - Contract documents, agreements
- **Word**: `.doc`, `.docx` - Legal documents
- **Excel**: `.csv`, `.xlsx` - Financial data, reports
- **Maximum Size**: 10MB per file

## 🔄 **Upload Process Flow**

```
1. File Selection/Drop
   ↓
2. File Validation
   ├── File type check
   ├── Size validation
   └── Error handling
   ↓
3. Upload to Backend
   ├── POST /upload endpoint
   ├── File storage in ./uploads/
   └── Version tracking
   ↓
4. Document Processing
   ├── LandingAI OCR extraction
   ├── Field mapping
   └── Database storage
   ↓
5. Drift Detection
   ├── Previous version comparison
   ├── Change detection
   └── Violation generation
   ↓
6. Real-time Updates
   ├── Dashboard refresh
   ├── New violations display
   └── Alert notifications
```

## 🎯 **Frontend Upload Interface**

### **Features**
- **Drag & Drop**: Drop files directly onto the upload area
- **File Browser**: Click "Choose Files" to browse and select
- **Multiple Files**: Upload several documents at once
- **Progress Tracking**: Real-time upload progress
- **Status Updates**: Success/error messages for each file
- **File Management**: Remove files from the upload queue

### **Visual Feedback**
- **Drag Over**: Blue border and background highlight
- **Uploading**: Spinning progress indicator
- **Success**: Green checkmark and success message
- **Error**: Red alert icon and error message

## 🔧 **Backend Processing**

### **Upload Endpoint** (`POST /upload`)
```python
@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contract_id: Optional[str] = None,
    document_type: Optional[str] = None
):
```

### **Processing Pipeline**
1. **File Storage**: Save to `./uploads/` directory
2. **Version Creation**: Generate unique version ID
3. **Background Processing**: Async document processing
4. **LandingAI Integration**: OCR and field extraction
5. **Database Storage**: Store metadata and extracted fields
6. **Drift Detection**: Compare with previous versions
7. **Violation Generation**: Create alerts for changes

## 📊 **Upload Status Tracking**

### **File States**
- **Pending**: File selected, waiting to upload
- **Uploading**: File being uploaded to backend
- **Processing**: Document being processed by LandingAI
- **Success**: Upload and processing completed
- **Error**: Upload or processing failed

### **Progress Indicators**
- **Progress Bar**: Visual upload progress (0-100%)
- **Status Icons**: Visual status indicators
- **Messages**: Detailed status messages
- **File Info**: File name, size, and type

## 🚨 **Error Handling**

### **Validation Errors**
- **Invalid File Type**: Only PDF, DOC, DOCX, CSV, XLSX allowed
- **File Too Large**: Maximum 10MB per file
- **Network Error**: Connection issues during upload

### **Processing Errors**
- **LandingAI Error**: OCR extraction failed
- **Database Error**: Storage operation failed
- **Pathway Error**: Stream processing failed

## 🔄 **Real-time Updates**

### **WebSocket Integration**
- **Live Updates**: Real-time processing status
- **New Violations**: Instant violation notifications
- **Dashboard Refresh**: Automatic data updates

### **Auto-refresh**
- **30-second intervals**: Regular data refresh
- **Manual refresh**: User-triggered updates
- **Live mode toggle**: Enable/disable real-time updates

## 📁 **File Storage Structure**

```
HWB/
├── uploads/           # Uploaded files
│   ├── document1.pdf
│   ├── contract2.docx
│   └── report3.csv
├── processed/         # Processed files
│   ├── extracted/
│   └── versions/
└── documents/         # Demo documents
    ├── LPA_v3.pdf
    ├── SideLetter_InstitutionA.pdf
    └── fees.csv
```

## 🎯 **Best Practices**

### **File Preparation**
- **Clear Scans**: Ensure documents are clearly scanned
- **Proper Format**: Use supported file formats
- **Reasonable Size**: Keep files under 10MB
- **Descriptive Names**: Use meaningful file names

### **Upload Process**
- **One at a Time**: Upload files individually for better tracking
- **Check Status**: Monitor upload and processing status
- **Handle Errors**: Address any validation or processing errors
- **Verify Results**: Check that documents appear in the dashboard

## 🔧 **Configuration**

### **Backend Settings** (`.env`)
```env
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,doc,docx,csv,xlsx
```

### **Frontend Settings** (`vite.config.ts`)
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

## 🚀 **Getting Started**

1. **Start Backend**: `python main.py`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Open Dashboard**: http://localhost:3000
4. **Upload Documents**: Use the upload component in the left sidebar
5. **Monitor Processing**: Watch for real-time updates and violations

## 🎉 **Result**

After uploading documents, you'll see:
- **Real-time processing status**
- **Extracted document fields**
- **Generated violations (if any)**
- **Updated dashboard metrics**
- **Live violation alerts**

The system automatically processes your documents and detects any changes or compliance violations!
