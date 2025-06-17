#!/usr/bin/env python3
"""
Simple disk monitoring script that checks disk usage and sends alerts to webhook.
"""

import os
import json
import time
import shutil
import requests
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiskMonitor:
    def __init__(self, webhook_url="http://localhost:5000/webhook/alert", threshold=80):
        self.webhook_url = webhook_url
        self.threshold = threshold
        self.hostname = os.uname().nodename
        
    def get_disk_usage(self, path="/"):
        """Get disk usage percentage for a given path."""
        try:
            total, used, free = shutil.disk_usage(path)
            usage_percent = (used / total) * 100
            return {
                'path': path,
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'usage_percent': round(usage_percent, 2)
            }
        except Exception as e:
            logger.error(f"Error getting disk usage for {path}: {e}")
            return None
    
    def create_alert(self, disk_info, severity="warning"):
        """Create alert data in Prometheus format."""
        current_time = datetime.now(timezone.utc).isoformat()
        
        alert_data = {
            "version": "4",
            "groupKey": f"{{}}:{{alertname=\"DiskSpaceHigh\"}}",
            "status": "firing",
            "receiver": "web.hook",
            "groupLabels": {
                "alertname": "DiskSpaceHigh"
            },
            "commonLabels": {
                "alertname": "DiskSpaceHigh",
                "instance": f"{self.hostname}:9100",
                "job": "disk_monitor",
                "severity": severity
            },
            "commonAnnotations": {
                "description": f"Disk space usage is {disk_info['usage_percent']}% on {disk_info['path']}",
                "summary": f"High disk usage detected on {self.hostname}"
            },
            "externalURL": "http://localhost:9090",
            "alerts": [{
                "status": "firing",
                "labels": {
                    "alertname": "DiskSpaceHigh",
                    "device": "disk0",
                    "fstype": "ext4",
                    "instance": f"{self.hostname}:9100",
                    "job": "disk_monitor",
                    "mountpoint": disk_info['path'],
                    "severity": severity
                },
                "annotations": {
                    "description": f"Disk space usage is {disk_info['usage_percent']}% on {disk_info['path']} ({self.hostname})",
                    "summary": f"High disk usage detected on {disk_info['path']} filesystem"
                },
                "startsAt": current_time,
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "http://localhost:9090/graph?g0.expr=disk_usage"
            }]
        }
        return alert_data
    
    def send_alert(self, alert_data):
        """Send alert to webhook endpoint."""
        try:
            response = requests.post(
                self.webhook_url,
                json=alert_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Alert sent successfully: {response.json()}")
                return True
            else:
                logger.error(f"Failed to send alert: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def check_and_alert(self, paths=["/"]):
        """Check disk usage and send alerts if threshold exceeded."""
        for path in paths:
            disk_info = self.get_disk_usage(path)
            if not disk_info:
                continue
                
            logger.info(f"Disk usage for {path}: {disk_info['usage_percent']}%")
            
            if disk_info['usage_percent'] > self.threshold:
                # Determine severity based on usage
                if disk_info['usage_percent'] > 90:
                    severity = "critical"
                elif disk_info['usage_percent'] > 85:
                    severity = "warning"
                else:
                    severity = "info"
                
                logger.warning(f"Disk usage threshold exceeded: {disk_info['usage_percent']}% > {self.threshold}%")
                alert_data = self.create_alert(disk_info, severity)
                self.send_alert(alert_data)
            else:
                logger.info(f"Disk usage normal: {disk_info['usage_percent']}% <= {self.threshold}%")
    
    def run_continuous(self, interval=60, paths=["/"]):
        """Run continuous monitoring."""
        logger.info(f"Starting continuous disk monitoring (threshold: {self.threshold}%, interval: {interval}s)")
        
        while True:
            try:
                self.check_and_alert(paths)
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Disk Space Monitor')
    parser.add_argument('--threshold', type=int, default=80, help='Disk usage threshold percentage (default: 80)')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--webhook', default='http://localhost:5000/webhook/alert', help='Webhook URL')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuously')
    parser.add_argument('--test', action='store_true', help='Send test alert regardless of disk usage')
    parser.add_argument('--paths', nargs='+', default=['/'], help='Paths to monitor (default: /)')
    
    args = parser.parse_args()
    
    monitor = DiskMonitor(webhook_url=args.webhook, threshold=args.threshold)
    
    if args.test:
        # Send a test alert
        logger.info("Sending test alert...")
        disk_info = monitor.get_disk_usage('/')
        if disk_info:
            # Force high usage for test
            disk_info['usage_percent'] = 85.5
            alert_data = monitor.create_alert(disk_info, "warning")
            monitor.send_alert(alert_data)
    elif args.once:
        monitor.check_and_alert(args.paths)
    else:
        monitor.run_continuous(args.interval, args.paths)

if __name__ == '__main__':
    main()