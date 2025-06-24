'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, CreditCard, Loader2 } from 'lucide-react'
import { loadStripe } from '@stripe/stripe-js'

interface UploadFormProps {
  userId: string
}

interface UploadedFile {
  file: File
  preview: string
  id: string
}

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

// SKU to price label mapping for clear user experience
const skuLabelMap = {
  SMOKE_TEST: '$1 Beta',
  SMALL: '$69',
  MEDIUM: '$99', 
  LARGE: '$189'
}

// Current SKU for Beta-0 testing
const CURRENT_SKU = 'SMOKE_TEST'

export default function UploadForm({ userId }: UploadFormProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).substr(2, 9),
    }))
    setUploadedFiles((prev) => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 10,
    maxSize: 10 * 1024 * 1024, // 10MB
  })

  const removeFile = (id: string) => {
    setUploadedFiles((prev) => {
      const fileToRemove = prev.find(f => f.id === id)
      if (fileToRemove) {
        URL.revokeObjectURL(fileToRemove.preview)
      }
      return prev.filter(f => f.id !== id)
    })
  }

  const uploadFiles = async () => {
    if (uploadedFiles.length === 0) return []

    setIsUploading(true)
    const uploadedUrls: string[] = []

    try {
      for (const { file, id } of uploadedFiles) {
        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 10) {
          setUploadProgress(prev => ({ ...prev, [id]: progress }))
          await new Promise(resolve => setTimeout(resolve, 100))
        }

        // In a real app, you'd upload to S3 here
        // For now, we'll just simulate successful upload
        const mockUrl = `https://petplantr-uploads.s3.amazonaws.com/${userId}/${id}-${file.name}`
        uploadedUrls.push(mockUrl)
      }

      return uploadedUrls
    } finally {
      setIsUploading(false)
      setUploadProgress({})
    }
  }

  const handlePayment = async () => {
    if (uploadedFiles.length === 0) {
      alert('Please upload at least one photo before proceeding to payment.')
      return
    }

    setIsProcessing(true)

    try {
      // First upload files
      const uploadedUrls = await uploadFiles()

      // Create checkout session
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: [
            {
              sku: CURRENT_SKU,
              quantity: 1,
            }
          ],
          metadata: {
            userId,
            photoUrls: uploadedUrls.join(','),
            photoCount: uploadedFiles.length.toString(),
          }
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const { checkoutUrl } = await response.json()

      // Redirect to Stripe Checkout
      window.location.href = checkoutUrl

    } catch (error) {
      console.error('Payment error:', error)
      alert('There was an error processing your payment. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const canProceedToPayment = uploadedFiles.length > 0 && !isUploading && !isProcessing

  return (
    <div className="space-y-8">
      {/* File Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-lg text-primary-600">Drop your photos here...</p>
        ) : (
          <div>
            <p className="text-lg text-gray-600 mb-2">
              Drag & drop pet photos here, or click to select
            </p>
            <p className="text-sm text-gray-500">
              Upload up to 10 photos (JPEG, PNG, WebP, max 10MB each)
            </p>
          </div>
        )}
      </div>

      {/* Uploaded Files Grid */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">
            Uploaded Photos ({uploadedFiles.length})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {uploadedFiles.map((uploadedFile) => (
              <div key={uploadedFile.id} className="relative group">
                <div className="aspect-square rounded-lg overflow-hidden bg-gray-100">
                  <img
                    src={uploadedFile.preview}
                    alt="Uploaded pet photo"
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* Upload Progress */}
                {isUploading && uploadProgress[uploadedFile.id] !== undefined && (
                  <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                    <div className="text-white text-center">
                      <Loader2 className="mx-auto h-6 w-6 animate-spin mb-2" />
                      <p className="text-sm">{uploadProgress[uploadedFile.id]}%</p>
                    </div>
                  </div>
                )}

                {/* Remove Button */}
                {!isUploading && (
                  <button
                    onClick={() => removeFile(uploadedFile.id)}
                    className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}

                {/* File Info */}
                <p className="mt-2 text-xs text-gray-500 truncate">
                  {uploadedFile.file.name}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Payment Section */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Order Summary</h3>
              <p className="text-sm text-gray-500">
                {uploadedFiles.length} photo{uploadedFiles.length !== 1 ? 's' : ''} uploaded
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-gray-900">$29.99</p>
              <p className="text-sm text-gray-500">includes shipping</p>
            </div>
          </div>

          <div className="border-t pt-4">
            <p className="text-sm text-gray-600 mb-4">
              Our AI will analyze your photos and create a custom 3D planter design. 
              You'll receive a preview within 24 hours and can request revisions before we print and ship.
            </p>

            <button
              onClick={handlePayment}
              disabled={!canProceedToPayment}
              className={`w-full flex items-center justify-center px-6 py-3 rounded-lg font-medium transition-colors ${
                canProceedToPayment
                  ? 'bg-primary-600 hover:bg-primary-700 text-white'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <CreditCard className="mr-2 h-5 w-5" />
                  {skuLabelMap[CURRENT_SKU]} - Pay with Stripe
                </>
              )}
            </button>

            <p className="text-xs text-gray-500 text-center mt-2">
              Secure payment powered by Stripe. We don't store your payment information.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
