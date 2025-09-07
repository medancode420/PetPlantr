import Link from 'next/link'
import { CheckCircle } from 'lucide-react'

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
        <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-6" />
        
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Payment Successful! 🎉
        </h1>
        
        <p className="text-gray-600 mb-6">
          Thank you for your order! We've received your payment and photos. 
          Our team will start creating your custom pet planter design.
        </p>
        
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h3 className="font-medium text-blue-900 mb-2">What happens next?</h3>
          <ul className="text-sm text-blue-800 text-left space-y-1">
            <li>• You'll receive an email confirmation shortly</li>
            <li>• Design preview ready within 24 hours</li>
            <li>• Approve design or request changes</li>
            <li>• 3D printing and shipping (3-5 business days)</li>
          </ul>
        </div>
        
        <Link
          href="/upload"
          className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          Create Another Planter
        </Link>
      </div>
    </div>
  )
}
