import Link from 'next/link'
import { AlertCircle } from 'lucide-react'

export default function ErrorPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
        <AlertCircle className="mx-auto h-16 w-16 text-red-500 mb-6" />
        
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Payment Failed
        </h1>
        
        <p className="text-gray-600 mb-6">
          We couldn't process your payment. This could be due to insufficient funds, 
          an expired card, or your bank declining the transaction.
        </p>
        
        <div className="bg-yellow-50 rounded-lg p-4 mb-6">
          <h3 className="font-medium text-yellow-900 mb-2">What you can try:</h3>
          <ul className="text-sm text-yellow-800 text-left space-y-1">
            <li>• Check your card details are correct</li>
            <li>• Try a different payment method</li>
            <li>• Contact your bank if the issue persists</li>
          </ul>
        </div>
        
        <div className="space-y-3">
          <Link
            href="/upload"
            className="block bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            Try Again
          </Link>
          
          <Link
            href="/"
            className="block bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-3 px-6 rounded-lg transition-colors"
          >
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}
