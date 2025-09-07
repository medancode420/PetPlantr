# PetPlantr Stripe + EventBridge Variables
# Story 3.4: Stripe + EventBridge prod toggle

variable "stripe_secret_key" {
  description = "Stripe production secret key"
  type        = string
  sensitive   = true
  default     = "sk_live_your_stripe_secret_key_here"
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook signing secret"
  type        = string
  sensitive   = true
  default     = "whsec_your_webhook_signing_secret_here"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "petplantr"
}
