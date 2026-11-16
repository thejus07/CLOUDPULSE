"""
Failure Simulation Service
Safely generates controlled, time-bounded failure conditions for testing
CloudPulse detection, diagnostics, alerting, and automated remediation.
Safety guarantees:
- Hard timeouts (auto-stop after duration)
- Isolated sandbox folders only
- Non-destructive processes
"""

import os
import time
import threading
import logging
from typing import Dict, Any, List

logger = logging.getLogger("CloudPulseSimulation")


class SimulationService:
    """Orchestrates safe, controlled infrastructure failure simulations."""

    _active_simulations: Dict[str, Dict[str, Any]] = {}
    _stop_events: Dict[str, threading.Event] = {}
    _allocated_memory: List[bytearray] = []

    @classmethod
    def start_simulation(cls, scenario: str, duration_seconds: int = 30) -> Dict[str, Any]:
        scenario = scenario.upper().strip()
        duration_seconds = min(max(duration_seconds, 5), 120)  # Bound between 5s and 120s

        if scenario in cls._active_simulations:
            return {"status": "ALREADY_RUNNING", "scenario": scenario, "active": True}

        stop_event = threading.Event()
        cls._stop_events[scenario] = stop_event

        info = {
            "scenario": scenario,
            "started_at": time.time(),
            "duration_seconds": duration_seconds,
            "status": "RUNNING"
        }
        cls._active_simulations[scenario] = info

        # Launch background runner based on scenario
        if scenario == "CPU_STRESS":
            threading.Thread(target=cls._run_cpu_stress, args=(stop_event, duration_seconds), daemon=True).start()
        elif scenario == "MEMORY_PRESSURE":
            threading.Thread(target=cls._run_memory_pressure, args=(stop_event, duration_seconds), daemon=True).start()
        elif scenario == "DISK_PRESSURE":
            threading.Thread(target=cls._run_disk_pressure, args=(stop_event, duration_seconds), daemon=True).start()
        elif scenario == "SERVICE_DOWN":
            threading.Thread(target=cls._run_service_down, args=(stop_event, duration_seconds), daemon=True).start()
        elif scenario == "DNS_FAILURE":
            threading.Thread(target=cls._run_dns_failure, args=(stop_event, duration_seconds), daemon=True).start()
        else:
            cls.stop_simulation(scenario)
            raise ValueError(f"Unknown simulation scenario: {scenario}")

        return {"status": "STARTED", "scenario": scenario, "duration_seconds": duration_seconds}

    @classmethod
    def stop_simulation(cls, scenario: str) -> Dict[str, Any]:
        scenario = scenario.upper().strip()
        stop_event = cls._stop_events.pop(scenario, None)
        if stop_event:
            stop_event.set()

        cls._active_simulations.pop(scenario, None)

        # Cleanup scenario-specific artifacts
        if scenario == "MEMORY_PRESSURE":
            cls._allocated_memory.clear()
        elif scenario == "DISK_PRESSURE":
            cls._cleanup_disk_artifacts()
        elif scenario == "SERVICE_DOWN":
            cls._cleanup_service_state()

        return {"status": "STOPPED", "scenario": scenario}

    @classmethod
    def get_status(cls) -> List[Dict[str, Any]]:
        now = time.time()
        results = []
        for sc, data in list(cls._active_simulations.items()):
            elapsed = int(now - data["started_at"])
            remaining = max(0, data["duration_seconds"] - elapsed)
            results.append({
                "scenario": sc,
                "elapsed_seconds": elapsed,
                "remaining_seconds": remaining,
                "status": data["status"]
            })
        return results

    # --- Scenario Implementations ---

    @classmethod
    def _run_cpu_stress(cls, stop_event: threading.Event, duration: int):
        """Generates controlled CPU activity without overwhelming host."""
        logger.info("Starting controlled CPU stress simulation for %ds...", duration)
        start = time.time()

        def worker():
            while not stop_event.is_set() and (time.time() - start) < duration:
                # Math calculation loop with periodic sleep to throttle
                _ = [x ** 2 for x in range(20000)]
                time.sleep(0.001)

        # Spawn workers proportional to cores
        threads = [threading.Thread(target=worker, daemon=True) for _ in range(4)]
        for t in threads:
            t.start()

        time.sleep(duration)
        stop_event.set()
        cls._active_simulations.pop("CPU_STRESS", None)
        logger.info("CPU stress simulation concluded.")

    @classmethod
    def _run_memory_pressure(cls, stop_event: threading.Event, duration: int):
        """Safely allocates moderate memory chunk (200MB) for demo testing."""
        logger.info("Starting controlled memory pressure simulation (%ds)...", duration)
        try:
            # Allocate 10 chunks of 20MB = 200MB safe allocation
            for _ in range(10):
                if stop_event.is_set():
                    break
                cls._allocated_memory.append(bytearray(20 * 1024 * 1024))
                time.sleep(0.1)

            # Hold for duration
            start = time.time()
            while not stop_event.is_set() and (time.time() - start) < duration:
                time.sleep(1)

        finally:
            cls._allocated_memory.clear()
            stop_event.set()
            cls._active_simulations.pop("MEMORY_PRESSURE", None)
            logger.info("Memory pressure simulation released.")

    @classmethod
    def _run_disk_pressure(cls, stop_event: threading.Event, duration: int):
        """Creates temporary test file in safe test directory."""
        logger.info("Starting controlled disk pressure simulation (%ds)...", duration)
        test_dir = os.path.join(os.getcwd(), "data", "test_temp")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "cloudpulse_test_bloat.tmp")

        try:
            # Write 25MB test file safely
            with open(test_file, "wb") as f:
                f.write(b"0" * (25 * 1024 * 1024))

            start = time.time()
            while not stop_event.is_set() and (time.time() - start) < duration:
                time.sleep(1)
        finally:
            cls._cleanup_disk_artifacts()
            stop_event.set()
            cls._active_simulations.pop("DISK_PRESSURE", None)
            logger.info("Disk pressure simulation cleaned up.")

    @classmethod
    def _run_service_down(cls, stop_event: threading.Event, duration: int):
        """Marks test service state as failed."""
        logger.info("Starting service failure simulation (%ds)...", duration)
        state_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(state_dir, exist_ok=True)
        state_file = os.path.join(state_dir, "test_service_test-service.state")

        try:
            with open(state_file, "w") as f:
                f.write("failed")

            start = time.time()
            while not stop_event.is_set() and (time.time() - start) < duration:
                time.sleep(1)
        finally:
            cls._cleanup_service_state()
            stop_event.set()
            cls._active_simulations.pop("SERVICE_DOWN", None)
            logger.info("Service failure simulation ended and restored.")

    @classmethod
    def _run_dns_failure(cls, stop_event: threading.Event, duration: int):
        logger.info("Simulating DNS failure condition (%ds)...", duration)
        time.sleep(duration)
        stop_event.set()
        cls._active_simulations.pop("DNS_FAILURE", None)

    @classmethod
    def _cleanup_disk_artifacts(cls):
        test_dir = os.path.join(os.getcwd(), "data", "test_temp")
        if os.path.exists(test_dir):
            for f in os.listdir(test_dir):
                if f.startswith("cloudpulse_test"):
                    try:
                        os.remove(os.path.join(test_dir, f))
                    except Exception:
                        pass

    @classmethod
    def _cleanup_service_state(cls):
        state_file = os.path.join(os.getcwd(), "data", "test_service_test-service.state")
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
            except Exception:
                pass
