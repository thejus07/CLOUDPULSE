"""
Unit tests for CloudPulse Automated Remediation Security Controls
"""

import os
import pytest
from backend.app.remediation.remediation_engine import RemediationEngine, SecurityViolation


def test_remediation_security_blocks_forbidden_service():
    with pytest.raises(SecurityViolation) as exc:
        RemediationEngine.execute_action(
            server_id="srv-sec-test",
            action_type="RESTART_SERVICE",
            parameters={"service": "unauthorized_arbitrary_service"},
            bypass_approval=True
        )
    assert "not in the approved remediation allowlist" in str(exc.value)


def test_remediation_security_blocks_unsafe_paths():
    with pytest.raises(SecurityViolation) as exc:
        RemediationEngine.execute_action(
            server_id="srv-sec-test",
            action_type="CLEAN_TEMP_FILES",
            parameters={"path": "/etc/passwd" if os.name != "nt" else "C:\\Windows\\System32"},
            bypass_approval=True
        )
    assert "outside configured safe cleanup paths" in str(exc.value)


def test_remediation_allowed_service_restart():
    res = RemediationEngine.execute_action(
        server_id="srv-sec-test",
        action_type="RESTART_SERVICE",
        parameters={"service": "nginx"},
        bypass_approval=True
    )
    assert res["status"] == "SUCCESS"
    assert res["action_type"] == "RESTART_SERVICE"
    assert "post_check" in res


def test_remediation_clean_temp_files():
    # Setup test file in allowed path
    test_dir = os.path.join(os.getcwd(), "data", "test_temp")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "cloudpulse_unit_test.tmp")
    with open(test_file, "w") as f:
        f.write("temporary junk log data")

    assert os.path.exists(test_file)

    res = RemediationEngine.execute_action(
        server_id="srv-sec-test",
        action_type="CLEAN_TEMP_FILES",
        parameters={"path": test_dir},
        bypass_approval=True
    )
    assert res["status"] == "SUCCESS"
    assert not os.path.exists(test_file)
