"""
Unit tests for CloudPulse Troubleshooting and Diagnostics Engine
"""

import pytest
from backend.app.diagnostics.cpu_diagnostics import CPUDiagnostics
from backend.app.diagnostics.memory_diagnostics import MemoryDiagnostics
from backend.app.diagnostics.disk_diagnostics import DiskDiagnostics
from backend.app.diagnostics.service_diagnostics import ServiceDiagnostics
from backend.app.diagnostics.network_diagnostics import NetworkDiagnostics
from backend.app.diagnostics.engine import DiagnosticEngine


def test_cpu_diagnostics_structure():
    diag = CPUDiagnostics(warning_threshold=70.0, critical_threshold=90.0)
    res = diag.run()

    assert res["diagnostic_type"] == "CPU"
    assert res["status"] in ("HEALTHY", "WARNING", "CRITICAL")
    assert "overall_cpu_percent" in res["findings"]
    assert "load_average" in res["findings"]
    assert "top_cpu_processes" in res["findings"]
    assert isinstance(res["recommendations"], list)


def test_memory_diagnostics_structure():
    diag = MemoryDiagnostics()
    res = diag.run()

    assert res["diagnostic_type"] == "MEMORY"
    assert "memory_percent" in res["findings"]
    assert "available_mb" in res["findings"]
    assert "top_memory_processes" in res["findings"]


def test_disk_diagnostics_structure():
    diag = DiskDiagnostics()
    res = diag.run()

    assert res["diagnostic_type"] == "DISK"
    assert "disk_percent" in res["findings"]
    assert "inode_usage" in res["findings"]
    assert "large_directories" in res["findings"]


def test_service_diagnostics():
    diag = ServiceDiagnostics(target_service="nginx")
    res = diag.run()

    assert res["diagnostic_type"] == "SERVICE"
    assert "services" in res["findings"]
    assert len(res["findings"]["services"]) >= 1


def test_network_diagnostics():
    diag = NetworkDiagnostics(target_domains=["localhost"])
    res = diag.run()

    assert res["diagnostic_type"] == "NETWORK"
    assert "dns" in res["findings"]
    assert "socket_tests" in res["findings"]


def test_diagnostic_engine_save_report():
    report = DiagnosticEngine.run_diagnostic("CPU", "srv-test-diag")
    assert report["id"].startswith("DIAG-")
    assert report["diagnostic_type"] == "CPU"
    assert report["execution_duration_ms"] >= 0
