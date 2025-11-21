#!/bin/bash
# Mautic Process Monitor - Detect and Kill Runaway Processes
# Created: October 18, 2025
# Purpose: Prevent resource exhaustion from runaway Mautic processes

# Thresholds
MAX_CPU_PERCENT=80
MAX_MEMORY_MB=1024
MAX_RUNTIME_MINUTES=30
LOG_FILE="/var/log/mautic_process_monitor.log"

# Email alert
EMAIL="w.aroca@insaing.com"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local subject="$1"
    local body="$2"
    echo "$body" | mail -s "$subject" "$EMAIL" 2>/dev/null || true
}

# Check for runaway Mautic PHP processes
check_mautic_processes() {
    # Find all PHP processes running Mautic commands
    while read -r pid cpu mem vsz rss etime cmd; do
        # Skip header
        [[ "$pid" == "PID" ]] && continue
        [[ -z "$pid" ]] && continue

        # Extract runtime in seconds
        runtime_seconds=$(echo "$etime" | awk -F: '{
            if (NF==3) print ($1*3600 + $2*60 + $3);
            else if (NF==2) print ($1*60 + $2);
            else print $1
        }')
        runtime_minutes=$((runtime_seconds / 60))

        # Check CPU threshold
        cpu_int=${cpu%.*}
        if [[ "$cpu_int" -gt "$MAX_CPU_PERCENT" ]]; then
            log "WARNING: PID $pid exceeds CPU threshold ($cpu% > $MAX_CPU_PERCENT%)"
            log "Command: $cmd"
            log "Runtime: ${runtime_minutes}min, Memory: ${mem}MB"

            # Kill if running too long
            if [[ "$runtime_minutes" -gt "$MAX_RUNTIME_MINUTES" ]]; then
                log "KILLING: PID $pid (runtime: ${runtime_minutes}min > ${MAX_RUNTIME_MINUTES}min)"
                kill -15 "$pid" 2>/dev/null && sleep 5 && kill -9 "$pid" 2>/dev/null
                send_alert "Mautic Runaway Process Killed - PID $pid" \
                    "Killed runaway Mautic process:\nPID: $pid\nCPU: $cpu%\nMemory: ${mem}MB\nRuntime: ${runtime_minutes}min\nCommand: $cmd"
            fi
        fi

        # Check memory threshold
        mem_int=${mem%.*}
        if [[ "$mem_int" -gt "$MAX_MEMORY_MB" ]]; then
            log "WARNING: PID $pid exceeds memory threshold (${mem}MB > ${MAX_MEMORY_MB}MB)"
            log "Command: $cmd"
            log "Runtime: ${runtime_minutes}min, CPU: $cpu%"

            # Kill if using too much memory
            log "KILLING: PID $pid (memory: ${mem}MB > ${MAX_MEMORY_MB}MB)"
            kill -15 "$pid" 2>/dev/null && sleep 5 && kill -9 "$pid" 2>/dev/null
            send_alert "Mautic High Memory Process Killed - PID $pid" \
                "Killed high-memory Mautic process:\nPID: $pid\nCPU: $cpu%\nMemory: ${mem}MB\nRuntime: ${runtime_minutes}min\nCommand: $cmd"
        fi

    done < <(ps aux | grep -E "php.*mautic:.*console" | grep -v grep | awk '{print $2, $3, $4, $5, $6, $10, substr($0, index($0,$11))}')
}

# Check for stuck processes (no CPU activity but still running)
check_stuck_processes() {
    while read -r pid cpu mem etime cmd; do
        [[ "$pid" == "PID" ]] && continue
        [[ -z "$pid" ]] && continue

        runtime_seconds=$(echo "$etime" | awk -F: '{
            if (NF==3) print ($1*3600 + $2*60 + $3);
            else if (NF==2) print ($1*60 + $2);
            else print $1
        }')
        runtime_minutes=$((runtime_seconds / 60))

        # If process has been running > 60 min with 0% CPU, it's stuck
        cpu_int=${cpu%.*}
        if [[ "$runtime_minutes" -gt 60 ]] && [[ "$cpu_int" -eq 0 ]]; then
            log "WARNING: Stuck process detected - PID $pid (runtime: ${runtime_minutes}min, CPU: 0%)"
            log "Command: $cmd"
            log "KILLING: PID $pid (stuck process)"
            kill -15 "$pid" 2>/dev/null && sleep 5 && kill -9 "$pid" 2>/dev/null
            send_alert "Mautic Stuck Process Killed - PID $pid" \
                "Killed stuck Mautic process:\nPID: $pid\nRuntime: ${runtime_minutes}min\nCPU: 0%\nMemory: ${mem}MB\nCommand: $cmd"
        fi
    done < <(ps aux | grep -E "php.*mautic:.*console" | grep -v grep | awk '{print $2, $3, $4, $10, substr($0, index($0,$11))}')
}

# Check total resource usage
check_total_usage() {
    total_cpu=$(ps aux | grep -E "php.*mautic" | grep -v grep | awk '{sum+=$3} END {print sum}')
    total_mem_mb=$(ps aux | grep -E "php.*mautic" | grep -v grep | awk '{sum+=$4*62000/100} END {print int(sum)}')
    process_count=$(ps aux | grep -E "php.*mautic" | grep -v grep | wc -l)

    total_cpu_int=${total_cpu%.*}

    if [[ "$total_cpu_int" -gt 150 ]] || [[ "$total_mem_mb" -gt 2048 ]] || [[ "$process_count" -gt 20 ]]; then
        log "ALERT: High total Mautic resource usage detected!"
        log "Total CPU: ${total_cpu}%, Total Memory: ${total_mem_mb}MB, Processes: $process_count"
        send_alert "Mautic High Resource Usage Alert" \
            "Mautic is using excessive resources:\n\nTotal CPU: ${total_cpu}%\nTotal Memory: ${total_mem_mb}MB\nProcess Count: $process_count\n\nPlease investigate."
    fi
}

# Main
log "=== Mautic Process Monitor Check ==="
check_mautic_processes
check_stuck_processes
check_total_usage
log "=== Check Complete ==="
