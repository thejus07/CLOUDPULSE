variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance size for CloudPulse monitored hosts"
  type        = string
  default     = "t3.medium"
}

variable "alert_email" {
  description = "Email address for SNS Incident alerts subscription"
  type        = string
  default     = "support-engineer@cloudpulse.internal"
}
