#!/bin/bash

# SMART health check script for manual testing
# This script checks disk health and outputs metrics

echo "=== SMART Disk Health Check ==="
echo

# Check if smartctl is available
if ! command -v smartctl &> /dev/null; then
    echo "Error: smartctl not found. Please install smartmontools:"
    echo "  brew install smartmontools"
    exit 1
fi

# Get list of disks
echo "Scanning for disks..."
DISKS=$(diskutil list | grep "/dev/disk" | grep "physical" | awk '{print $1}')

if [[ -z "$DISKS" ]]; then
    echo "No physical disks found"
    exit 1
fi

echo "Found disks: $DISKS"
echo

# Check each disk
for disk in $DISKS; do
    echo "=== Checking $disk ==="
    
    # Get basic disk info
    echo "Disk Information:"
    diskutil info $disk | grep -E "(Device Node|Media Name|Total Size|Protocol)" || true
    echo
    
    # Check SMART capability
    echo "SMART Capability Check:"
    if smartctl -i $disk | grep -q "SMART support is: Available"; then
        echo "✓ SMART supported"
        
        if smartctl -i $disk | grep -q "SMART support is: Enabled"; then
            echo "✓ SMART enabled"
        else
            echo "⚠ SMART disabled - attempting to enable..."
            sudo smartctl -s on $disk
        fi
    else
        echo "✗ SMART not supported on $disk"
        continue
    fi
    echo
    
    # Check SMART health
    echo "SMART Health Status:"
    health_output=$(smartctl -H $disk 2>/dev/null)
    if echo "$health_output" | grep -q "SMART overall-health self-assessment test result: PASSED"; then
        echo "✓ SMART health: PASSED"
    elif echo "$health_output" | grep -q "SMART overall-health self-assessment test result: FAILED"; then
        echo "✗ SMART health: FAILED"
    else
        echo "? SMART health: Unknown"
    fi
    echo
    
    # Show key SMART attributes
    echo "Key SMART Attributes:"
    smartctl -A $disk 2>/dev/null | grep -E "(Reallocated_Sector_Ct|Spin_Retry_Count|End-to-End_Error|Reported_Uncorrect|Command_Timeout|Current_Pending_Sector|Offline_Uncorrectable)" || echo "No critical attributes found"
    echo
    
    # Temperature check
    echo "Temperature:"
    temp_info=$(smartctl -A $disk 2>/dev/null | grep -i temperature | head -1)
    if [[ -n "$temp_info" ]]; then
        echo "$temp_info"
    else
        echo "Temperature information not available"
    fi
    echo
    
    echo "----------------------------------------"
    echo
done

# Test the metrics endpoint
echo "=== Testing Metrics Endpoint ==="
if curl -s http://localhost:5000/smart_metrics | head -10; then
    echo
    echo "✓ Metrics endpoint is working"
else
    echo "✗ Metrics endpoint not available"
    echo "Make sure the webhook server is running: python3 webhook_server/app.py"
fi

echo
echo "=== Summary ==="
echo "To monitor continuously:"
echo "  1. Ensure all services are running: ./scripts/start_services.sh"
echo "  2. Check Prometheus targets: http://localhost:9090/targets"
echo "  3. View SMART metrics: http://localhost:5000/smart_metrics"
echo "  4. Check alerts: http://localhost:9093"
