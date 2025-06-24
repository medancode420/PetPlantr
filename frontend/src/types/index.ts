export interface CartItem {
  sku: string
  quantity: number
}

export interface CheckoutRequest {
  items: CartItem[]
  metadata?: {
    userId?: string
    photoUrls?: string
    photoCount?: string
    [key: string]: string | undefined
  }
}

export interface CheckoutResponse {
  checkoutUrl: string
}

export interface UploadedFile {
  file: File
  preview: string
  id: string
}
