#!/usr/bin/env python3
"""
Generate comprehensive test alerts for storage monitoring system.
Creates various types of storage alerts to test Slack integration and database storage.
"""

import requests
import json
from datetime import datetime, timedelta
import time

def send_alert(webhook_url, alert_data):
    """Send alert to webhook endpoint."""
    try:
        # Wrap in Prometheus AlertManager format
        payload = {
            'version': '4',
            'groupKey': f'{alert_data["alertname"]}:{alert_data["labels"].get("severity", "unknown")}',
            'status': alert_data['status'],
            'receiver': 'storage-webhook',
            'groupLabels': {'alertname': alert_data['alertname']},
            'commonLabels': alert_data['labels'],
            'commonAnnotations': alert_data['annotations'],
            'externalURL': 'http://localhost:9093',
            'alerts': [alert_data]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✓ Sent: {alert_data['alertname']} ({alert_data['labels']['severity']})")
            return True
        else:
            print(f"✗ Failed: {alert_data['alertname']} - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error sending {alert_data['alertname']}: {e}")
        return False

def generate_test_alerts():
    """Generate comprehensive test alerts."""
    webhook_url = "http://localhost:5000/webhook/alert"
    current_time = datetime.now()
    
    alerts = [
        # Critical Disk Space Alert
        {
            'alertname': 'DiskSpaceCritical',
            'status': 'firing',
            'labels': {
                'severity': 'critical',
                'instance': 'storage-server-01',
                'device': '/dev/nvme0n1p1',
                'mountpoint': '/var/lib/data',
                'fstype': 'ext4',
                'alerttype': 'storage'
            },
            'annotations': {
                'summary': 'Critical disk space usage on primary data partition',
                'description': 'Disk usage on /var/lib/data has reached 95% capacity. Immediate action required to prevent service disruption. Available space: 2.1GB of 500GB total.',
                'runbook_url': 'https://docs.company.com/runbooks/disk-space-critical',
                'dashboard_url': 'http://localhost:3000',
                'impact': 'High - Service degradation imminent',
                'resolution': 'Clean up logs, archive old data, or expand storage'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000/device/nvme0n1p1'
        },
        
        # Warning Disk Space Alert
        {
            'alertname': 'DiskSpaceWarning',
            'status': 'firing',
            'labels': {
                'severity': 'warning',
                'instance': 'storage-server-02',
                'device': '/dev/sdb1',
                'mountpoint': '/opt/backups',
                'fstype': 'xfs',
                'alerttype': 'storage'
            },
            'annotations': {
                'summary': 'Disk space usage approaching threshold on backup partition',
                'description': 'Disk usage on /opt/backups is at 82% capacity. Monitor closely and plan cleanup activities. Used: 410GB of 500GB total.',
                'runbook_url': 'https://docs.company.com/runbooks/disk-space-warning'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000/device/sdb1'
        },
        
        # Critical Inode Usage Alert
        {
            'alertname': 'InodeExhaustion',
            'status': 'firing',
            'labels': {
                'severity': 'critical',
                'instance': 'web-server-03',
                'mountpoint': '/var/log',
                'fstype': 'ext4',
                'alerttype': 'storage'
            },
            'annotations': {
                'summary': 'Inode exhaustion detected on log partition',
                'description': 'Inode usage on /var/log has reached 98%. File creation will fail soon. Used inodes: 524,280 of 524,288 total. Free inodes: 8',
                'runbook_url': 'https://docs.company.com/runbooks/inode-exhaustion',
                'impact': 'Critical - Cannot create new files',
                'resolution': 'Delete unnecessary files, especially small log files'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000'
        },
        
        # High I/O Wait Alert
        {
            'alertname': 'HighIOWait',
            'status': 'firing',
            'labels': {
                'severity': 'warning',
                'instance': 'database-server-04',
                'alerttype': 'performance'
            },
            'annotations': {
                'summary': 'High I/O wait time detected',
                'description': 'I/O wait percentage is 45%, indicating storage bottlenecks. This may impact application performance. Current load average: 8.2, 7.8, 6.9',
                'runbook_url': 'https://docs.company.com/runbooks/high-io-wait',
                'impact': 'Medium - Performance degradation'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000'
        },
        
        # SMART Hardware Warning
        {
            'alertname': 'SMARTWarning',
            'status': 'firing',
            'labels': {
                'severity': 'warning',
                'instance': 'storage-server-05',
                'device': '/dev/sdc',
                'alerttype': 'hardware'
            },
            'annotations': {
                'summary': 'SMART attribute threshold exceeded',
                'description': 'Disk /dev/sdc shows declining SMART attributes. Reallocated sectors: 45 (threshold: 36). Consider replacing disk during next maintenance window.',
                'runbook_url': 'https://docs.company.com/runbooks/smart-warning',
                'impact': 'Low - Preventive maintenance required'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000'
        },
        
        # Filesystem Error Alert
        {
            'alertname': 'FilesystemErrors',
            'status': 'firing',
            'labels': {
                'severity': 'critical',
                'instance': 'app-server-06',
                'mountpoint': '/opt/applications',
                'fstype': 'ext4',
                'alerttype': 'storage'
            },
            'annotations': {
                'summary': 'Filesystem errors detected',
                'description': 'Multiple filesystem errors detected on /opt/applications. Error count: 12 in the last hour. This may indicate hardware failure or corruption.',
                'runbook_url': 'https://docs.company.com/runbooks/filesystem-errors',
                'impact': 'High - Data integrity risk'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000'
        },
        
        # Storage Pool Warning
        {
            'alertname': 'StoragePoolDegraded',
            'status': 'firing',
            'labels': {
                'severity': 'warning',
                'instance': 'raid-controller-01',
                'pool': 'data-pool-01',
                'alerttype': 'storage'
            },
            'annotations': {
                'summary': 'Storage pool operating in degraded mode',
                'description': 'RAID storage pool data-pool-01 is degraded. One disk failed, redundancy compromised. Replace failed disk: /dev/sde',
                'runbook_url': 'https://docs.company.com/runbooks/raid-degraded'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000'
        },
        
        # Network Storage Alert
        {
            'alertname': 'NFSMountIssue',
            'status': 'firing',
            'labels': {
                'severity': 'critical',
                'instance': 'compute-node-07',
                'mountpoint': '/shared/data',
                'fstype': 'nfs',
                'alerttype': 'network'
            },
            'annotations': {
                'summary': 'NFS mount becoming unresponsive',
                'description': 'NFS mount /shared/data showing high latency and intermittent failures. Network storage may be overloaded or experiencing connectivity issues.',
                'runbook_url': 'https://docs.company.com/runbooks/nfs-issues'
            },
            'startsAt': current_time.isoformat(),
            'generatorURL': 'http://localhost:3000'
        }
    ]
    
    # Send alerts with small delays
    print("Generating comprehensive storage test alerts...")
    print("=" * 60)
    
    sent_count = 0
    for i, alert in enumerate(alerts, 1):
        print(f"[{i}/{len(alerts)}] ", end="")
        if send_alert(webhook_url, alert):
            sent_count += 1
        
        # Small delay between alerts
        if i < len(alerts):
            time.sleep(0.5)
    
    print("=" * 60)
    print(f"Alert generation complete: {sent_count}/{len(alerts)} alerts sent successfully")
    
    # Generate a resolved alert to test resolution flow
    time.sleep(1)
    print("\nSending resolved alert...")
    
    resolved_alert = {
        'alertname': 'DiskSpaceWarning',
        'status': 'resolved',
        'labels': {
            'severity': 'warning',
            'instance': 'storage-server-02',
            'device': '/dev/sdb1',
            'mountpoint': '/opt/backups',
            'fstype': 'xfs',
            'alerttype': 'storage'
        },
        'annotations': {
            'summary': 'Disk space usage has returned to normal levels',
            'description': 'Cleanup activities completed. Disk usage on /opt/backups reduced to 65%. Alert resolved automatically.',
            'resolution': 'Old backup files archived and removed'
        },
        'startsAt': (current_time - timedelta(hours=2)).isoformat(),
        'endsAt': datetime.now().isoformat(),
        'generatorURL': 'http://localhost:3000/device/sdb1'
    }
    
    if send_alert(webhook_url, resolved_alert):
        sent_count += 1
    
    return sent_count

if __name__ == '__main__':
    total_sent = generate_test_alerts()
    print(f"\nTotal alerts processed: {total_sent}")
    print("Check your Slack channel and dashboard at http://localhost:3000 for the alerts!")