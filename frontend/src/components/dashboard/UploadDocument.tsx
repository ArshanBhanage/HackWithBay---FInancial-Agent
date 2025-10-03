import { useState, useRef } from 'react'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { uploadContract } from '@/services/api'

interface UploadedFile {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  message?: string
}

export function UploadDocument() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const acceptedFileTypes = ['.pdf', '.doc', '.docx', '.csv', '.xlsx']
  const maxFileSize = 10 * 1024 * 1024 // 10MB

  const validateFile = (file: File): string | null => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!acceptedFileTypes.includes(fileExtension)) {
      return `File type ${fileExtension} is not supported. Please upload: ${acceptedFileTypes.join(', ')}`
    }
    
    if (file.size > maxFileSize) {
      return `File size ${(file.size / 1024 / 1024).toFixed(1)}MB exceeds maximum size of ${maxFileSize / 1024 / 1024}MB`
    }
    
    return null
  }

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return

    Array.from(files).forEach(file => {
      const validationError = validateFile(file)
      
      if (validationError) {
        setUploadedFiles(prev => [...prev, {
          file,
          status: 'error',
          progress: 0,
          message: validationError
        }])
        return
      }

      const newFile: UploadedFile = {
        file,
        status: 'pending',
        progress: 0
      }

      setUploadedFiles(prev => [...prev, newFile])
      uploadFile(newFile)
    })
  }

  const uploadFile = async (uploadedFile: UploadedFile) => {
    const fileIndex = uploadedFiles.findIndex(f => f.file === uploadedFile.file)
    
    // Update status to uploading
    setUploadedFiles(prev => prev.map((f, index) => 
      index === fileIndex ? { ...f, status: 'uploading', progress: 0 } : f
    ))

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadedFiles(prev => prev.map((f, index) => {
          if (index === fileIndex && f.status === 'uploading' && f.progress < 90) {
            return { ...f, progress: f.progress + 10 }
          }
          return f
        }))
      }, 200)

      const result = await uploadContract(uploadedFile.file)
      
      clearInterval(progressInterval)
      
      // Update status to success
      setUploadedFiles(prev => prev.map((f, index) => 
        index === fileIndex ? { 
          ...f, 
          status: 'success', 
          progress: 100,
          message: `Uploaded successfully: ${result.version_id}`
        } : f
      ))

    } catch (error) {
      // Update status to error
      setUploadedFiles(prev => prev.map((f, index) => 
        index === fileIndex ? { 
          ...f, 
          status: 'error', 
          progress: 0,
          message: error instanceof Error ? error.message : 'Upload failed'
        } : f
      ))
    }
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'uploading':
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      default:
        return <FileText className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'success':
        return 'text-green-600'
      case 'error':
        return 'text-red-600'
      case 'uploading':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Upload Documents</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-700 mb-2">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Supports: {acceptedFileTypes.join(', ')} (max 10MB each)
          </p>
          <Button 
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            className="gap-2"
          >
            <Upload className="w-4 h-4" />
            Choose Files
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={acceptedFileTypes.join(',')}
            onChange={(e) => handleFileSelect(e.target.files)}
            className="hidden"
          />
        </div>

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700">Uploaded Files</h4>
            {uploadedFiles.map((uploadedFile, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3 flex-1">
                  {getStatusIcon(uploadedFile.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {uploadedFile.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(uploadedFile.file.size / 1024 / 1024).toFixed(1)} MB
                    </p>
                    {uploadedFile.message && (
                      <p className={`text-xs ${getStatusColor(uploadedFile.status)}`}>
                        {uploadedFile.message}
                      </p>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                {uploadedFile.status === 'uploading' && (
                  <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${uploadedFile.progress}%` }}
                    />
                  </div>
                )}

                {/* Remove Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Instructions */}
        <div className="text-xs text-gray-500 space-y-1">
          <p><strong>Supported formats:</strong> PDF, DOC, DOCX, CSV, XLSX</p>
          <p><strong>Maximum file size:</strong> 10MB per file</p>
          <p><strong>Processing:</strong> Documents are automatically processed for drift detection</p>
        </div>
      </CardContent>
    </Card>
  )
}
