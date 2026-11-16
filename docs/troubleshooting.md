# CloudPulse Troubleshooting & Linux Engineering Guide

This document details practical support engineering diagnostic procedures, Linux commands, and root-cause analysis methodologies for scenarios monitored by CloudPulse.

---

## 1. High CPU Utilization & Runaway Processes

### Symptoms
- Load average higher than the number of CPU cores.
- CloudPulse alert: `Critical CPU Saturation (>90%)`.
- High response latency or connection timeouts.

### Manual Linux Triage Commands
```bash
# 1. Inspect top CPU consuming threads
top -b -n 1 | head -n 20
htop

# 2. View top 10 CPU-consuming processes ordered by %CPU
ps aux --sort=-%cpu | head -n 11

# 3. Check thread states for a specific runaway PID
ps -T -p <PID>

# 4. Check whether CPU is in user mode, system/kernel mode, or I/O wait
vmstat 1 5
# Look at 'us' (user), 'sy' (system), 'wa' (iowait), 'id' (idle)
```

### CloudPulse Automated Investigation
1. `CPUDiagnostics` extracts top process PIDs, CPU%, and command lines.
2. Identifies whether saturation is concentrated in a single rogue process or distributed across threads.
3. Recommends targeted process investigation or horizontal instance scaling.

---

## 2. High Memory Utilization & Out of Memory (OOM)

### Symptoms
- Memory utilization > 92%.
- Swap space heavily utilized with high disk paging.
- Linux OOM-killer terminating critical daemon processes.

### Manual Linux Triage Commands
```bash
# 1. Check physical and swap memory breakdown
free -h

# 2. Identify top 10 memory-consuming processes by RSS (Resident Set Size)
ps aux --sort=-rss | head -n 11

# 3. Inspect kernel ring buffer for OOM killer invocations
dmesg -T | grep -i -E "oom|out of memory|killed process"

# 4. Detailed virtual memory and page table statistics
cat /proc/meminfo
```

### CloudPulse Automated Investigation
1. `MemoryDiagnostics` calculates active vs available memory and swap footprint.
2. Cross-references running processes against memory percentages to pinpoint memory leaks.
3. Suggests buffer cache clearing or worker pool optimization.

---

## 3. Disk Space Saturation & Inode Exhaustion

### Symptoms
- Write operations fail with `No space left on device` even when `df -h` appears to have space (indicative of inode depletion).
- Database or log writers crashing.

### Manual Linux Triage Commands
```bash
# 1. Check disk space usage across all mounted filesystems
df -h

# 2. Check inode utilization (Crucial for detecting millions of small files)
df -i

# 3. Locate the top 10 largest directories on the root partition
du -h --max-depth=1 /var | sort -hr | head -n 10

# 4. Find open files that were deleted but space is held open by a running process
lsof +L1
```

### CloudPulse Automated Remediation
1. `DiskDiagnostics` scans partitions and tests inode tables via `os.statvfs`.
2. Locates bloated files and directories in designated log and temp directories.
3. Invokes allowlisted `CLEAN_TEMP_FILES` or `ROTATE_LOGS` with strict directory boundary validation.

---

## 4. Systemd Service Failures

### Symptoms
- Daemon stops accepting socket connections.
- Exit codes like `status=1/FAILURE`, `status=137` (SIGKILL/OOM), or `status=127` (command not found).

### Manual Linux Triage Commands
```bash
# 1. Check systemd unit status
systemctl status nginx.service

# 2. List all currently failed units
systemctl list-units --state=failed

# 3. View recent log output from journalctl
journalctl -u nginx.service -n 50 --no-pager

# 4. Test port conflicts (Address already in use)
ss -tulnp | grep :80
lsof -i :80
```

### CloudPulse Automated Remediation
1. `ServiceDiagnostics` parses journalctl logs for error signatures (`Address already in use`, `Permission denied`, `OOM`).
2. If safe, executes allowlisted `RESTART_SERVICE`.
3. Performs post-check query using `systemctl is-active` to verify daemon restored.
