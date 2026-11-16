"""
CloudPulse Configuration Module
Handles application settings, thresholds, database URLs, and environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of Project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base Configuration."""
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    SECRET_KEY = os.getenv("SECRET_KEY", "cloudpulse-dev-secret-key-32890")
    API_KEY = os.getenv("API_KEY", "cloudpulse-internal-api-key-2026")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")

    # Database
    DEFAULT_SQLITE_PATH = BASE_DIR / "data" / "cloudpulse.db"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")

    # Monitoring Thresholds (percentages)
    THRESHOLD_CPU_WARNING = float(os.getenv("THRESHOLD_CPU_WARNING", 75.0))
    THRESHOLD_CPU_CRITICAL = float(os.getenv("THRESHOLD_CPU_CRITICAL", 90.0))
    THRESHOLD_MEMORY_WARNING = float(os.getenv("THRESHOLD_MEMORY_WARNING", 80.0))
    THRESHOLD_MEMORY_CRITICAL = float(os.getenv("THRESHOLD_MEMORY_CRITICAL", 92.0))
    THRESHOLD_DISK_WARNING = float(os.getenv("THRESHOLD_DISK_WARNING", 80.0))
    THRESHOLD_DISK_CRITICAL = float(os.getenv("THRESHOLD_DISK_CRITICAL", 90.0))

    METRIC_INTERVAL_SECONDS = int(os.getenv("METRIC_COLLECTION_INTERVAL_SECONDS", 10))

    # Automated Remediation Security Controls
    REMEDIATION_ENABLED = os.getenv("REMEDIATION_ENABLED", "true").lower() in ("true", "1", "yes")
    REMEDIATION_REQUIRE_APPROVAL = os.getenv("REMEDIATION_REQUIRE_APPROVAL", "false").lower() in ("true", "1", "yes")
    
    # Strict allowlist of services permitted for restart
    ALLOWED_SERVICES = [
        s.strip() for s in os.getenv(
            "REMEDIATION_ALLOWED_SERVICES",
            "nginx,apache2,postgresql,redis,cloudpulse-worker,test-service"
        ).split(",") if s.strip()
    ]
    
    # Strict allowlist of directory paths permitted for cleanup
    ALLOWED_TEMP_PATHS = [
        p.strip() for p in os.getenv(
            "REMEDIATION_ALLOWED_TEMP_PATHS",
            f"{BASE_DIR / 'data' / 'test_temp'},/tmp/cloudpulse_test,/tmp/cloudpulse_cache"
        ).split(",") if p.strip()
    ]

    # AWS Integration Settings
    ENABLE_AWS_INTEGRATION = os.getenv("ENABLE_AWS_INTEGRATION", "false").lower() in ("true", "1", "yes")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_CLOUDWATCH_NAMESPACE = os.getenv("AWS_CLOUDWATCH_NAMESPACE", "CloudPulse/Infrastructure")
    AWS_SNS_INCIDENT_TOPIC_ARN = os.getenv("AWS_SNS_INCIDENT_TOPIC_ARN", "")


config = Config()
