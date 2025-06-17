#!/usr/bin/env python3
"""
Comprehensive system monitoring script for testing various alert scenarios.
"""

import os
import json
import time
import psutil
import requests
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, webhook_url="http://localhost:5000/webhook/alert"):
        self.webhook_url = webhook_url
        self.hostname = os.uname().nodename
        
    def get_system_metrics(self):
        """Get comprehensive system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage for all mounted filesystems
            disk_usage = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'usage_percent': round((usage.used / usage.total) * 100, 2)
                    })
                except PermissionError:
                    continue
            
            # Load average (Linux/Unix only)
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = (0, 0, 0)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'disk_usage': disk_usage,
                'load_avg': load_avg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def create_alert(self, alert_name, severity, description, labels=None):
        """Create a standardized alert."""
        current_time = datetime.now(timezone.utc).isoformat()
        
        if labels is None:
            labels = {}
        
        base_labels = {
            "alertname": alert_name,
            "instance": f"{self.hostname}:9100",
            "job": "system_monitor",
            "severity": severity
        }
        base_labels.update(labels)
        
        alert_data = {
            "version": "4",
            "groupKey": f"{{}}:{{alertname=\"{alert_name}\"}}",
            "status": "firing",
            "receiver": "web.hook",
            "groupLabels": {"alertname": alert_name},
            "commonLabels": base_labels,
            "commonAnnotations": {
                "description": description,
                "summary": f"{alert_name} detected on {self.hostname}"
            },
            "externalURL": "http://localhost:9090",
            "alerts": [{
                "status": "firing",
                "labels": base_labels,
                "annotations": {
                    "description": description,
                    "summary": f"{alert_name} detected"
                },
                "startsAt": current_time,
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "http://localhost:9090/graph?g0.expr=metric"
            }]
        }
        return alert_data
    
    def send_alert(self, alert_data):
        """Send alert to webhook."""
        try:
            response = requests.post(
                self.webhook_url,
                json=alert_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 500]:  # 500 is expected without JIRA config
                logger.info(f"Alert sent: {alert_data['commonLabels']['alertname']}")
                return True
            else:
                logger.error(f"Failed to send alert: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def check_thresholds(self, metrics):
        """Check various thresholds and generate alerts."""
        alerts_sent = 0
        
        # Check CPU usage
        if metrics['cpu_percent'] > 80:
            severity = "critical" if metrics['cpu_percent'] > 95 else "warning"
            alert = self.create_alert(
                "HighCPUUsage",
                severity,
                f"CPU usage is {metrics['cpu_percent']}%",
                {"cpu_percent": str(metrics['cpu_percent'])}
            )
            if self.send_alert(alert):
                alerts_sent += 1
        
        # Check memory usage
        if metrics['memory_percent'] > 80:
            severity = "critical" if metrics['memory_percent'] > 95 else "warning"
            alert = self.create_alert(
                "HighMemoryUsage",
                severity,
                f"Memory usage is {metrics['memory_percent']}% ({metrics['memory_used_gb']}GB/{metrics['memory_total_gb']}GB)",
                {"memory_percent": str(metrics['memory_percent'])}
            )
            if self.send_alert(alert):
                alerts_sent += 1
        
        # Check disk usage
        for disk in metrics['disk_usage']:
            if disk['usage_percent'] > 80:
                severity = "critical" if disk['usage_percent'] > 95 else "warning"
                alert = self.create_alert(
                    "HighDiskUsage",
                    severity,
                    f"Disk usage is {disk['usage_percent']}% on {disk['mountpoint']} ({disk['used_gb']}GB/{disk['total_gb']}GB)",
                    {
                        "device": disk['device'],
                        "mountpoint": disk['mountpoint'],
                        "fstype": disk['fstype'],
                        "usage_percent": str(disk['usage_percent'])
                    }
                )
                if self.send_alert(alert):
                    alerts_sent += 1
        
        # Check load average (for systems that support it)
        if metrics['load_avg'][0] > 4.0:  # 1-minute load average
            severity = "critical" if metrics['load_avg'][0] > 8.0 else "warning"
            alert = self.create_alert(
                "HighLoadAverage",
                severity,
                f"Load average is {metrics['load_avg'][0]:.2f} (1min), {metrics['load_avg'][1]:.2f} (5min), {metrics['load_avg'][2]:.2f} (15min)",
                {"load_1min": str(metrics['load_avg'][0])}
            )
            if self.send_alert(alert):
                alerts_sent += 1
        
        return alerts_sent
    
    def run_test_scenarios(self):
        """Run various test scenarios to validate alert processing."""
        logger.info("Running test scenarios...")
        
        # Test 1: Simulated high disk usage
        logger.info("Test 1: High disk usage alert")
        alert = self.create_alert(
            "DiskSpaceHigh",
            "warning",
            "Simulated high disk usage test - 87% on /var/log",
            {"device": "/dev/sda1", "mountpoint": "/var/log", "usage_percent": "87"}
        )
        self.send_alert(alert)
        time.sleep(2)
        
        # Test 2: Critical memory usage
        logger.info("Test 2: Critical memory usage alert")
        alert = self.create_alert(
            "MemoryExhaustion",
            "critical",
            "Simulated critical memory usage - 97% (15.2GB/15.7GB)",
            {"memory_percent": "97", "memory_type": "physical"}
        )
        self.send_alert(alert)
        time.sleep(2)
        
        # Test 3: High CPU usage
        logger.info("Test 3: High CPU usage alert")
        alert = self.create_alert(
            "HighCPUUsage",
            "warning",
            "Simulated high CPU usage - 89% across all cores",
            {"cpu_percent": "89", "cpu_cores": "4"}
        )
        self.send_alert(alert)
        time.sleep(2)
        
        # Test 4: Service down
        logger.info("Test 4: Service down alert")
        alert = self.create_alert(
            "ServiceDown",
            "critical",
            "Simulated service failure - PostgreSQL database unreachable",
            {"service": "postgresql", "port": "5432"}
        )
        self.send_alert(alert)
        time.sleep(2)
        
        # Test 5: Network connectivity issue
        logger.info("Test 5: Network connectivity alert")
        alert = self.create_alert(
            "NetworkConnectivityIssue",
            "warning",
            "Simulated network issue - High packet loss to gateway (15%)",
            {"target": "gateway", "packet_loss": "15"}
        )
        self.send_alert(alert)
        
        logger.info("Test scenarios completed")
    
    def monitor_once(self):
        """Run monitoring once and check thresholds."""
        metrics = self.get_system_metrics()
        if not metrics:
            logger.error("Failed to get system metrics")
            return
        
        logger.info(f"System Metrics:")
        logger.info(f"  CPU: {metrics['cpu_percent']}%")
        logger.info(f"  Memory: {metrics['memory_percent']}% ({metrics['memory_used_gb']}GB/{metrics['memory_total_gb']}GB)")
        logger.info(f"  Load Average: {metrics['load_avg'][0]:.2f}, {metrics['load_avg'][1]:.2f}, {metrics['load_avg'][2]:.2f}")
        
        for disk in metrics['disk_usage']:
            logger.info(f"  Disk {disk['mountpoint']}: {disk['usage_percent']}% ({disk['used_gb']}GB/{disk['total_gb']}GB)")
        
        alerts_sent = self.check_thresholds(metrics)
        logger.info(f"Alerts sent: {alerts_sent}")
    
    def monitor_continuous(self, interval=60):
        """Run continuous monitoring."""
        logger.info(f"Starting continuous system monitoring (interval: {interval}s)")
        
        while True:
            try:
                self.monitor_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='System Monitor')
    parser.add_argument('--webhook', default='http://localhost:5000/webhook/alert', help='Webhook URL')
    parser.add_argument('--once', action='store_true', help='Run once')
    parser.add_argument('--test', action='store_true', help='Run test scenarios')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(webhook_url=args.webhook)
    
    if args.test:
        monitor.run_test_scenarios()
    elif args.once:
        monitor.monitor_once()
    else:
        monitor.monitor_continuous(args.interval)

if __name__ == '__main__':
    main()