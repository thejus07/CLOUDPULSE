"""
AWS Integration Layer
Provides EC2 metadata discovery (IMDSv2), CloudWatch metric publishing,
SNS alerting, and SSM Run Command execution.
Gracefully operates in Local / Simulation mode when AWS credentials or EC2 environment are not present.
"""

import logging
import requests
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from typing import Dict, Any, List, Optional
from backend.app.config import config

logger = logging.getLogger("CloudPulseAWS")


class AWSClient:
    """Manages AWS interactions using IAM roles and standard SDK paths."""

    _cached_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def get_ec2_metadata(cls) -> Dict[str, Any]:
        """
        Retrieves EC2 instance metadata securely using IMDSv2.
        Falls back to local host metadata when not running inside AWS EC2.
        """
        if cls._cached_metadata:
            return cls._cached_metadata

        imds_token_url = "http://169.254.169.254/latest/api/token"
        imds_meta_url = "http://169.254.169.254/latest/meta-data"

        try:
            # 1. Fetch IMDSv2 session token with 1 second timeout
            token_resp = requests.put(
                imds_token_url,
                headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
                timeout=1.0
            )
            if token_resp.status_code == 200:
                token = token_resp.text
                headers = {"X-aws-ec2-metadata-token": token}

                # Helper to safely read an IMDS key
                def _get_item(path: str) -> str:
                    try:
                        r = requests.get(f"{imds_meta_url}/{path}", headers=headers, timeout=1.0)
                        return r.text if r.status_code == 200 else ""
                    except Exception:
                        return ""

                meta = {
                    "is_ec2": True,
                    "instance_id": _get_item("instance-id") or "i-unknown",
                    "instance_type": _get_item("instance-type") or "t3.medium",
                    "ami_id": _get_item("ami-id") or "ami-unknown",
                    "availability_zone": _get_item("placement/availability-zone") or "us-east-1a",
                    "region": _get_item("placement/region") or config.AWS_REGION,
                    "local_ipv4": _get_item("local-ipv4") or "127.0.0.1",
                    "public_ipv4": _get_item("public-ipv4") or ""
                }
                cls._cached_metadata = meta
                return meta

        except Exception:
            pass

        # Fallback for local development or non-AWS environments
        meta = {
            "is_ec2": False,
            "instance_id": "i-local-dev-node",
            "instance_type": "on-premises-workstation",
            "ami_id": "ami-local-emulated",
            "availability_zone": f"{config.AWS_REGION}a (emulated)",
            "region": config.AWS_REGION,
            "local_ipv4": "127.0.0.1",
            "public_ipv4": "127.0.0.1"
        }
        cls._cached_metadata = meta
        return meta

    @classmethod
    def publish_cloudwatch_metric(
        cls,
        metric_name: str,
        value: float,
        unit: str = "Percent",
        dimensions: List[Dict[str, str]] = None
    ) -> bool:
        """Publishes custom telemetry metric to AWS CloudWatch."""
        if not config.ENABLE_AWS_INTEGRATION:
            logger.debug("[AWS-Simulated] CloudWatch Metric %s = %s %s", metric_name, value, unit)
            return True

        try:
            cw = boto3.client("cloudwatch", region_name=config.AWS_REGION)
            metric_data = {
                "MetricName": metric_name,
                "Value": float(value),
                "Unit": unit
            }
            if dimensions:
                metric_data["Dimensions"] = dimensions

            cw.put_metric_data(
                Namespace=config.AWS_CLOUDWATCH_NAMESPACE,
                MetricData=[metric_data]
            )
            logger.info("Published metric %s to CloudWatch namespace %s", metric_name, config.AWS_CLOUDWATCH_NAMESPACE)
            return True
        except (NoCredentialsError, ClientError) as e:
            logger.warning("AWS CloudWatch publish skipped (No valid AWS credentials/IAM role): %s", e)
            return False
        except Exception as e:
            logger.error("Error publishing CloudWatch metric: %s", e)
            return False

    @classmethod
    def publish_sns_alert(cls, topic_arn: str, subject: str, message: str) -> bool:
        """Publishes an alert notification to an AWS SNS topic."""
        if not config.ENABLE_AWS_INTEGRATION or not topic_arn:
            logger.debug("[AWS-Simulated] SNS Alert to %s: [%s] %s", topic_arn, subject, message[:60])
            return True

        try:
            sns = boto3.client("sns", region_name=config.AWS_REGION)
            sns.publish(
                TopicArn=topic_arn,
                Subject=subject[:100],
                Message=message
            )
            logger.info("Published incident alert to SNS topic %s", topic_arn)
            return True
        except (NoCredentialsError, ClientError) as e:
            logger.warning("AWS SNS publish skipped (No credentials/role): %s", e)
            return False
        except Exception as e:
            logger.error("Error publishing to SNS: %s", e)
            return False

    @classmethod
    def execute_ssm_command(cls, instance_ids: List[str], command: str) -> Dict[str, Any]:
        """
        Executes a command across an EC2 fleet via AWS Systems Manager (SSM) Run Command.
        """
        if not config.ENABLE_AWS_INTEGRATION:
            return {
                "status": "SIMULATED",
                "command_id": "cmd-simulated-ssm-001",
                "instance_ids": instance_ids,
                "message": "AWS integration disabled; SSM command simulated."
            }

        try:
            ssm = boto3.client("ssm", region_name=config.AWS_REGION)
            resp = ssm.send_command(
                InstanceIds=instance_ids,
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
                TimeoutSeconds=30
            )
            return {
                "status": "SUBMITTED",
                "command_id": resp["Command"]["CommandId"],
                "instance_ids": instance_ids
            }
        except (NoCredentialsError, ClientError) as e:
            logger.warning("SSM command execution skipped (No credentials): %s", e)
            return {"status": "FAILED", "error": str(e)}

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns health and connectivity status of the AWS integration subsystem."""
        meta = cls.get_ec2_metadata()
        has_credentials = False
        try:
            session = boto3.Session()
            has_credentials = session.get_credentials() is not None
        except Exception:
            has_credentials = False

        return {
            "aws_integration_enabled": config.ENABLE_AWS_INTEGRATION,
            "region": config.AWS_REGION,
            "is_running_on_ec2": meta.get("is_ec2", False),
            "instance_id": meta.get("instance_id"),
            "availability_zone": meta.get("availability_zone"),
            "has_iam_credentials": has_credentials,
            "cloudwatch_namespace": config.AWS_CLOUDWATCH_NAMESPACE,
            "sns_topic_configured": bool(config.AWS_SNS_INCIDENT_TOPIC_ARN)
        }
