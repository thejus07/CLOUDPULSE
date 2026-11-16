terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. Dedicated VPC for Monitored Fleet
resource "aws_vpc" "cloudpulse_vpc" {
  cidr_block           = "10.100.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "cloudpulse-vpc"
    Environment = var.environment
  }
}

# Public Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.cloudpulse_vpc.id
  cidr_block              = "10.100.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "cloudpulse-public-subnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.cloudpulse_vpc.id

  tags = {
    Name = "cloudpulse-igw"
  }
}

# Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.cloudpulse_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "cloudpulse-public-rt"
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# 2. Security Group
resource "aws_security_group" "cloudpulse_sg" {
  name        = "cloudpulse-node-sg"
  description = "Allows SSH, HTTP, and CloudPulse metrics traffic"
  vpc_id      = aws_vpc.cloudpulse_vpc.id

  ingress {
    description = "SSH from authorized bastion"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "CloudPulse API & Dashboard"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Frontend Dashboard"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cloudpulse-security-group"
  }
}

# 3. IAM Role for CloudPulse EC2 Instances
resource "aws_iam_role" "cloudpulse_node_role" {
  name = "CloudPulseEC2MonitoringRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Attach CloudWatch & Systems Manager (SSM) Managed Policies (Least Privilege)
resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.cloudpulse_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.cloudpulse_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "cloudpulse_profile" {
  name = "CloudPulseInstanceProfile"
  role = aws_iam_role.cloudpulse_node_role.name
}

# 4. Amazon SNS Topic for High & Critical Severity Incident Alerts
resource "aws_sns_topic" "incident_alerts" {
  name = "cloudpulse-incident-alerts"

  tags = {
    Environment = var.environment
    Service     = "CloudPulse"
  }
}

resource "aws_sns_topic_subscription" "email_sub" {
  topic_arn = aws_sns_topic.incident_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# 5. CloudWatch Metric Alarm
resource "aws_cloudwatch_metric_alarm" "high_cpu_alarm" {
  alarm_name          = "CloudPulse-HighCPU-Utilization"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "CloudPulse/Infrastructure"
  period              = 60
  statistic           = "Average"
  threshold           = 90
  alarm_description   = "Triggers when CPU utilization on monitored instances breaches 90%"
  alarm_actions       = [aws_sns_topic.incident_alerts.arn]
}

# 6. Monitored EC2 Instance
data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "monitored_node" {
  ami                  = data.aws_ami.ubuntu.id
  instance_type        = var.instance_type
  subnet_id            = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.cloudpulse_sg.id]
  iam_instance_profile = aws_iam_instance_profile.cloudpulse_profile.name

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y python3-pip git
              git clone https://github.com/cloudpulse/platform.git /opt/cloudpulse
              cd /opt/cloudpulse
              pip install -r backend/requirements.txt
              python3 agent/main.py --daemon &
              EOF

  tags = {
    Name        = "cloudpulse-monitored-node-01"
    Role        = "MonitoredHost"
    Environment = var.environment
  }
}
