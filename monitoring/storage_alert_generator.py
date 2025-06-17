#!/usr/bin/env python3
"""
Storage Alert Generator for Enterprise Storage Monitoring
Monitors storage metrics and sends alerts to webhook endpoint for Slack/database integration.
"""

import os
import sys
import json
import time
import psutil
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

# Add parent directory to path to import storage metrics
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitoring.storage_metrics import StorageMetricsCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AlertThresholds:
    """Storage alert thresholds configuration."""
    disk_usage_warning: float = 80.0
    disk_usage_critical: float = 90.0
    inode_usage_warning: float = 80.0
    inode_usage_critical: float = 90.0
    io_wait_warning: float = 20.0
    io_wait_critical: float = 40.0
    load_average_warning: float = 5.0
    load_average_critical: float = 10.0
    read_latency_warning: float = 100.0  # ms
    read_latency_critical: float = 200.0  # ms
    write_latency_warning: float = 100.0  # ms
    write_latency_critical: float = 200.0  # ms

class StorageAlertGenerator:
    """Generates storage alerts based on real system metrics."""
    
    def __init__(self, webhook_url: str = "http://localhost:5000/webhook/alert"):
        self.webhook_url = webhook_url
        self.thresholds = AlertThresholds()
        self.metrics_collector = StorageMetricsCollector()
        self.alert_history = {}  # Track sent alerts to avoid spam
        
    def check_disk_usage(self) -> List[Dict[str, Any]]:
        """Check disk usage and generate alerts if thresholds exceeded."""
        alerts = []
        
        try:
            # Get disk usage from psutil
            disk_partitions = psutil.disk_partitions()
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (usage.used / usage.total) * 100
                    
                    # Skip if usage is very low (likely virtual filesystems)
                    if usage_percent < 1.0:
                        continue
                    
                    severity = None
                    if usage_percent >= self.thresholds.disk_usage_critical:
                        severity = 'critical'
                    elif usage_percent >= self.thresholds.disk_usage_warning:
                        severity = 'warning'
                    
                    if severity:
                        alert_key = f"disk_usage_{partition.device}_{severity}"
                        
                        # Check if we've sent this alert recently (avoid spam)
                        if not self._should_send_alert(alert_key):
                            continue
                        
                        alert = {
                            'alertname': 'DiskSpaceUsage',
                            'status': 'firing',
                            'labels': {
                                'severity': severity,
                                'instance': 'localhost',
                                'device': partition.device,
                                'mountpoint': partition.mountpoint,
                                'fstype': partition.fstype,
                                'alerttype': 'storage'
                            },
                            'annotations': {
                                'summary': f'Disk space usage is {severity} on {partition.mountpoint}',
                                'description': f'Disk usage on {partition.mountpoint} ({partition.device}) is {usage_percent:.1f}%, which exceeds the {severity} threshold of {self.thresholds.disk_usage_critical if severity == "critical" else self.thresholds.disk_usage_warning}%.\n\nUsed: {self._format_bytes(usage.used)}\nTotal: {self._format_bytes(usage.total)}\nAvailable: {self._format_bytes(usage.free)}',
                                'runbook_url': 'https://example.com/runbooks/disk-space',
                                'dashboard_url': 'http://localhost:3000'
                            },
                            'startsAt': datetime.now().isoformat(),
                            'generatorURL': f'http://localhost:3000/device/{partition.device.replace("/", "_")}'
                        }
                        alerts.append(alert)
                        self._mark_alert_sent(alert_key)
                        
                except PermissionError:
                    # Skip inaccessible partitions
                    continue
                except Exception as e:
                    logger.warning(f"Error checking disk usage for {partition.mountpoint}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking disk usage: {e}")
        
        return alerts
    
    def check_inode_usage(self) -> List[Dict[str, Any]]:
        """Check inode usage and generate alerts if thresholds exceeded."""
        alerts = []
        
        try:
            # Get comprehensive storage metrics
            metrics = self.metrics_collector.collect_all_metrics()
            
            if metrics.get('filesystem_layer', {}).get('inode_usage'):
                for mountpoint, inode_data in metrics['filesystem_layer']['inode_usage'].items():
                    usage_percent = inode_data.get('inode_usage_percent', 0)
                    
                    severity = None
                    if usage_percent >= self.thresholds.inode_usage_critical:
                        severity = 'critical'
                    elif usage_percent >= self.thresholds.inode_usage_warning:
                        severity = 'warning'
                    
                    if severity:
                        alert_key = f"inode_usage_{mountpoint}_{severity}"
                        
                        if not self._should_send_alert(alert_key):
                            continue
                        
                        alert = {
                            'alertname': 'InodeUsage',
                            'status': 'firing',
                            'labels': {
                                'severity': severity,
                                'instance': 'localhost',
                                'mountpoint': mountpoint,
                                'alerttype': 'storage'
                            },
                            'annotations': {
                                'summary': f'Inode usage is {severity} on {mountpoint}',
                                'description': f'Inode usage on {mountpoint} is {usage_percent:.1f}%, which exceeds the {severity} threshold.\n\nUsed inodes: {inode_data.get("used_inodes", 0)}\nTotal inodes: {inode_data.get("total_inodes", 0)}\nFree inodes: {inode_data.get("free_inodes", 0)}',
                                'runbook_url': 'https://example.com/runbooks/inode-usage'
                            },
                            'startsAt': datetime.now().isoformat(),
                            'generatorURL': 'http://localhost:3000'
                        }
                        alerts.append(alert)
                        self._mark_alert_sent(alert_key)
                        
        except Exception as e:
            logger.error(f"Error checking inode usage: {e}")
        
        return alerts
    
    def check_io_performance(self) -> List[Dict[str, Any]]:
        """Check I/O performance metrics and generate alerts."""
        alerts = []
        
        try:
            # Get system load average
            load_avg = os.getloadavg()
            current_load = load_avg[0]  # 1-minute load average
            
            severity = None
            if current_load >= self.thresholds.load_average_critical:
                severity = 'critical'
            elif current_load >= self.thresholds.load_average_warning:
                severity = 'warning'
            
            if severity:
                alert_key = f"load_average_{severity}"
                
                if self._should_send_alert(alert_key):
                    alert = {
                        'alertname': 'HighSystemLoad',
                        'status': 'firing',
                        'labels': {
                            'severity': severity,
                            'instance': 'localhost',
                            'alerttype': 'performance'
                        },
                        'annotations': {
                            'summary': f'System load average is {severity}',
                            'description': f'1-minute load average is {current_load:.2f}, which exceeds the {severity} threshold of {self.thresholds.load_average_critical if severity == "critical" else self.thresholds.load_average_warning}.\n\nLoad averages: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}',
                            'runbook_url': 'https://example.com/runbooks/high-load'
                        },
                        'startsAt': datetime.now().isoformat(),
                        'generatorURL': 'http://localhost:3000'
                    }
                    alerts.append(alert)
                    self._mark_alert_sent(alert_key)
            
            # Check I/O wait percentage
            try:
                cpu_times = psutil.cpu_times_percent(interval=1)
                if hasattr(cpu_times, 'iowait'):
                    io_wait = cpu_times.iowait
                    
                    severity = None
                    if io_wait >= self.thresholds.io_wait_critical:
                        severity = 'critical'
                    elif io_wait >= self.thresholds.io_wait_warning:
                        severity = 'warning'
                    
                    if severity:
                        alert_key = f"io_wait_{severity}"
                        
                        if self._should_send_alert(alert_key):
                            alert = {
                                'alertname': 'HighIOWait',
                                'status': 'firing',
                                'labels': {
                                    'severity': severity,
                                    'instance': 'localhost',
                                    'alerttype': 'performance'
                                },
                                'annotations': {
                                    'summary': f'I/O wait time is {severity}',
                                    'description': f'I/O wait percentage is {io_wait:.1f}%, indicating potential storage bottlenecks. This exceeds the {severity} threshold of {self.thresholds.io_wait_critical if severity == "critical" else self.thresholds.io_wait_warning}%.',
                                    'runbook_url': 'https://example.com/runbooks/high-io-wait'
                                },
                                'startsAt': datetime.now().isoformat(),
                                'generatorURL': 'http://localhost:3000'
                            }
                            alerts.append(alert)
                            self._mark_alert_sent(alert_key)
            except:
                pass  # I/O wait not available on all systems
                
        except Exception as e:
            logger.error(f"Error checking I/O performance: {e}")
        
        return alerts
    
    def check_storage_health(self) -> List[Dict[str, Any]]:
        """Check overall storage health and generate summary alerts."""
        alerts = []
        
        try:
            metrics = self.metrics_collector.collect_all_metrics()
            health_metrics = metrics.get('health_layer', {})
            
            # Check for filesystem errors
            if health_metrics.get('filesystem_errors', 0) > 0:
                alert_key = "filesystem_errors"
                
                if self._should_send_alert(alert_key):
                    alert = {
                        'alertname': 'FilesystemErrors',
                        'status': 'firing',
                        'labels': {
                            'severity': 'warning',
                            'instance': 'localhost',
                            'alerttype': 'storage'
                        },
                        'annotations': {
                            'summary': 'Filesystem errors detected',
                            'description': f'Detected {health_metrics["filesystem_errors"]} filesystem errors. This may indicate storage hardware issues or filesystem corruption.',
                            'runbook_url': 'https://example.com/runbooks/filesystem-errors'
                        },
                        'startsAt': datetime.now().isoformat(),
                        'generatorURL': 'http://localhost:3000'
                    }
                    alerts.append(alert)
                    self._mark_alert_sent(alert_key)
            
            # Check SMART status if available
            smart_status = health_metrics.get('smart_overall_health', 'unknown')
            if smart_status not in ['PASSED', 'unknown']:
                alert_key = f"smart_health_{smart_status}"
                
                if self._should_send_alert(alert_key):
                    alert = {
                        'alertname': 'SMARTHealthWarning',
                        'status': 'firing',
                        'labels': {
                            'severity': 'critical',
                            'instance': 'localhost',
                            'alerttype': 'hardware'
                        },
                        'annotations': {
                            'summary': 'SMART health check failed',
                            'description': f'SMART health status is {smart_status}. This indicates potential hardware failure. Immediate attention required.',
                            'runbook_url': 'https://example.com/runbooks/smart-failure'
                        },
                        'startsAt': datetime.now().isoformat(),
                        'generatorURL': 'http://localhost:3000'
                    }
                    alerts.append(alert)
                    self._mark_alert_sent(alert_key)
                    
        except Exception as e:
            logger.error(f"Error checking storage health: {e}")
        
        return alerts
    
    def _should_send_alert(self, alert_key: str, cooldown_minutes: int = 15) -> bool:
        """Check if an alert should be sent based on cooldown period."""
        if alert_key not in self.alert_history:
            return True
        
        last_sent = self.alert_history[alert_key]
        cooldown_period = timedelta(minutes=cooldown_minutes)
        
        return datetime.now() - last_sent > cooldown_period
    
    def _mark_alert_sent(self, alert_key: str):
        """Mark an alert as sent with current timestamp."""
        self.alert_history[alert_key] = datetime.now()
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to webhook endpoint."""
        try:
            # Wrap alert in Prometheus AlertManager format
            payload = {
                'version': '4',
                'groupKey': f'{alert["alertname"]}:{alert["labels"].get("severity", "unknown")}',
                'status': alert['status'],
                'receiver': 'storage-webhook',
                'groupLabels': {
                    'alertname': alert['alertname']
                },
                'commonLabels': alert['labels'],
                'commonAnnotations': alert['annotations'],
                'externalURL': 'http://localhost:9093',
                'alerts': [alert]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent alert: {alert['alertname']}")
                return True
            else:
                logger.error(f"Failed to send alert {alert['alertname']}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert {alert['alertname']}: {e}")
            return False
    
    def run_monitoring_cycle(self) -> int:
        """Run a complete monitoring cycle and return number of alerts sent."""
        logger.info("Starting storage monitoring cycle")
        
        all_alerts = []
        
        # Collect all types of alerts
        all_alerts.extend(self.check_disk_usage())
        all_alerts.extend(self.check_inode_usage())
        all_alerts.extend(self.check_io_performance())
        all_alerts.extend(self.check_storage_health())
        
        # Send alerts
        sent_count = 0
        for alert in all_alerts:
            if self.send_alert(alert):
                sent_count += 1
        
        if sent_count > 0:
            logger.info(f"Monitoring cycle complete: {sent_count} alerts sent")
        else:
            logger.info("Monitoring cycle complete: No alerts triggered")
        
        return sent_count
    
    def run_continuous(self, interval_seconds: int = 300):
        """Run continuous monitoring with specified interval."""
        logger.info(f"Starting continuous storage monitoring (interval: {interval_seconds}s)")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")

def main():
    """Main entry point for storage alert generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Storage Alert Generator')
    parser.add_argument('--webhook-url', default='http://localhost:5000/webhook/alert',
                       help='Webhook URL for sending alerts')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring interval in seconds (default: 300)')
    parser.add_argument('--once', action='store_true',
                       help='Run once instead of continuously')
    
    args = parser.parse_args()
    
    generator = StorageAlertGenerator(webhook_url=args.webhook_url)
    
    if args.once:
        alerts_sent = generator.run_monitoring_cycle()
        print(f"Monitoring complete: {alerts_sent} alerts sent")
    else:
        generator.run_continuous(interval_seconds=args.interval)

if __name__ == '__main__':
    main()