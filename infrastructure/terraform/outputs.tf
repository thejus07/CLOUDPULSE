output "instance_id" {
  description = "EC2 Instance ID of the monitored server"
  value       = aws_instance.monitored_node.id
}

output "instance_public_ip" {
  description = "Public IP address of the monitored instance"
  value       = aws_instance.monitored_node.public_ip
}

output "sns_topic_arn" {
  description = "ARN of the Amazon SNS alert notification topic"
  value       = aws_sns_topic.incident_alerts.arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.cloudpulse_vpc.id
}
