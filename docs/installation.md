# CloudPulse Installation & Deployment Guide

This guide covers local development, Docker Compose orchestration, and AWS EC2 deployment.

---

## 1. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone https://github.com/cloudpulse/platform.git
cd CLOUDPULSE

# 2. Run automated setup script
bash scripts/setup.sh
# (On Windows PowerShell: python -m pip install -r backend/requirements.txt)

# 3. Configure environment
cp .env.example .env

# 4. Start CloudPulse Backend API
python -m backend.app.main
# The API will be reachable at http://localhost:5000/api

# 5. In a second terminal, start the Monitoring Agent
python agent/main.py --daemon --interval 10

# 6. In a third terminal, start the Frontend Dashboard
cd frontend
npm install
npm run dev
# The React dashboard will be accessible at http://localhost:3000
```

---

## 2. Docker & Docker Compose Deployment

To run a production-ready stack with PostgreSQL, the Flask backend, and the monitoring agent:

```bash
# Start all containers in background
docker compose up -d

# Verify container health
docker compose ps

# View backend logs
docker compose logs -f backend

# Stop stack
docker compose down
```

---

## 3. AWS Infrastructure Deployment (Terraform)

CloudPulse includes Terraform definitions to provision a dedicated VPC, Security Group, IAM Role, SNS Alert Topic, and an EC2 instance with CloudPulse pre-installed:

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform plan

# Apply infrastructure (requires AWS credentials)
terraform apply -auto-approve
```

### AWS EC2 IAM Policy Requirements
When hosting CloudPulse on EC2, attach an IAM role with least-privilege policies:
- `CloudWatchAgentServerPolicy` (for `cloudwatch:PutMetricData`)
- `AmazonSSMManagedInstanceCore` (for remote command orchestration)
- `sns:Publish` on the alert topic ARN
