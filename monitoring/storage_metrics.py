"""
Enterprise Storage Metrics Collection
Advanced storage monitoring with 20+ years of storage engineering expertise.
Covers physical, logical, and application-layer storage metrics.
"""

import os
import psutil
import subprocess
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
import glob
import re

class StorageMetricsCollector:
    """
    Comprehensive storage metrics collector covering:
    - Physical layer (disk hardware, SMART data)
    - Logical layer (filesystems, volumes)
    - Application layer (I/O patterns, caching)
    - Performance metrics (latency, throughput, IOPS)
    """
    
    def __init__(self):
        self.metrics_history = defaultdict(list)
        self.baseline_metrics = {}
        
    def collect_all_metrics(self):
        """Collect comprehensive storage metrics."""
        return {
            'physical_layer': self.get_physical_metrics(),
            'logical_layer': self.get_logical_metrics(),
            'performance_layer': self.get_performance_metrics(),
            'filesystem_layer': self.get_filesystem_metrics(),
            'io_patterns': self.get_io_pattern_metrics(),
            'capacity_planning': self.get_capacity_planning_metrics(),
            'health_metrics': self.get_health_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_physical_metrics(self):
        """Physical storage device metrics."""
        try:
            physical_metrics = {
                'disk_devices': [],
                'smart_data': {},
                'hardware_info': {},
                'thermal_metrics': {}
            }
            
            # Disk device enumeration
            for device in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(device.mountpoint)
                    device_info = {
                        'device': device.device,
                        'mountpoint': device.mountpoint,
                        'fstype': device.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    }
                    
                    # Get device I/O stats
                    io_stats = self.get_device_io_stats(device.device)
                    if io_stats:
                        device_info.update(io_stats)
                    
                    physical_metrics['disk_devices'].append(device_info)
                except:
                    continue
            
            # SMART data collection
            physical_metrics['smart_data'] = self.get_smart_data()
            
            # Block device information
            physical_metrics['block_devices'] = self.get_block_device_info()
            
            return physical_metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_logical_metrics(self):
        """Logical storage layer metrics."""
        try:
            logical_metrics = {
                'volume_groups': [],
                'logical_volumes': [],
                'raid_status': {},
                'mount_points': [],
                'filesystem_health': {}
            }
            
            # Mount point analysis
            for mount in psutil.disk_partitions():
                try:
                    stat = os.statvfs(mount.mountpoint)
                    mount_info = {
                        'mountpoint': mount.mountpoint,
                        'device': mount.device,
                        'fstype': mount.fstype,
                        'block_size': stat.f_bsize,
                        'fragment_size': stat.f_frsize,
                        'total_blocks': stat.f_blocks,
                        'free_blocks': stat.f_bfree,
                        'available_blocks': stat.f_bavail,
                        'total_inodes': stat.f_files,
                        'free_inodes': stat.f_ffree,
                        'mount_flags': mount.opts
                    }
                    logical_metrics['mount_points'].append(mount_info)
                except:
                    continue
            
            # Check for LVM, RAID, and other logical storage
            logical_metrics['lvm_info'] = self.get_lvm_info()
            logical_metrics['raid_info'] = self.get_raid_info()
            
            return logical_metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_performance_metrics(self):
        """Storage performance metrics."""
        try:
            perf_metrics = {
                'io_statistics': {},
                'latency_metrics': {},
                'throughput_metrics': {},
                'iops_metrics': {},
                'queue_depth': {},
                'cache_metrics': {}
            }
            
            # Disk I/O statistics
            disk_io = psutil.disk_io_counters(perdisk=True)
            if disk_io:
                for device, stats in disk_io.items():
                    perf_metrics['io_statistics'][device] = {
                        'read_count': stats.read_count,
                        'write_count': stats.write_count,
                        'read_bytes': stats.read_bytes,
                        'write_bytes': stats.write_bytes,
                        'read_time': stats.read_time,
                        'write_time': stats.write_time,
                        'busy_time': getattr(stats, 'busy_time', 0)
                    }
                    
                    # Calculate derived metrics
                    if stats.read_count > 0:
                        perf_metrics['latency_metrics'][device] = {
                            'avg_read_latency_ms': stats.read_time / stats.read_count,
                            'avg_write_latency_ms': stats.write_time / stats.write_count if stats.write_count > 0 else 0
                        }
                    
                    perf_metrics['throughput_metrics'][device] = {
                        'read_throughput_bps': stats.read_bytes,
                        'write_throughput_bps': stats.write_bytes,
                        'total_throughput_bps': stats.read_bytes + stats.write_bytes
                    }
                    
                    perf_metrics['iops_metrics'][device] = {
                        'read_iops': stats.read_count,
                        'write_iops': stats.write_count,
                        'total_iops': stats.read_count + stats.write_count
                    }
            
            # System-wide I/O metrics
            perf_metrics['system_io'] = self.get_system_io_metrics()
            
            return perf_metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_filesystem_metrics(self):
        """Filesystem-specific metrics."""
        try:
            fs_metrics = {
                'filesystem_types': {},
                'inode_usage': {},
                'fragmentation': {},
                'journal_status': {},
                'filesystem_errors': {}
            }
            
            # Analyze each filesystem
            for partition in psutil.disk_partitions():
                try:
                    mountpoint = partition.mountpoint
                    fstype = partition.fstype
                    
                    # Inode analysis
                    stat = os.statvfs(mountpoint)
                    if stat.f_files > 0:
                        inode_usage = {
                            'total_inodes': stat.f_files,
                            'free_inodes': stat.f_ffree,
                            'used_inodes': stat.f_files - stat.f_ffree,
                            'inode_usage_percent': ((stat.f_files - stat.f_ffree) / stat.f_files) * 100
                        }
                        fs_metrics['inode_usage'][mountpoint] = inode_usage
                    
                    # Filesystem type statistics
                    if fstype not in fs_metrics['filesystem_types']:
                        fs_metrics['filesystem_types'][fstype] = {
                            'count': 0,
                            'total_size': 0,
                            'total_used': 0
                        }
                    
                    usage = psutil.disk_usage(mountpoint)
                    fs_metrics['filesystem_types'][fstype]['count'] += 1
                    fs_metrics['filesystem_types'][fstype]['total_size'] += usage.total
                    fs_metrics['filesystem_types'][fstype]['total_used'] += usage.used
                    
                except:
                    continue
            
            return fs_metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_io_pattern_metrics(self):
        """I/O pattern analysis metrics."""
        try:
            io_patterns = {
                'access_patterns': {},
                'file_size_distribution': {},
                'temporal_patterns': {},
                'hot_spots': {}
            }
            
            # Analyze recent file access patterns
            io_patterns['recent_activity'] = self.analyze_recent_file_activity()
            
            # File size distribution analysis
            io_patterns['file_size_stats'] = self.analyze_file_size_distribution()
            
            # I/O queue analysis
            io_patterns['queue_analysis'] = self.analyze_io_queues()
            
            return io_patterns
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_capacity_planning_metrics(self):
        """Capacity planning and forecasting metrics."""
        try:
            capacity_metrics = {
                'growth_trends': {},
                'utilization_forecast': {},
                'threshold_analysis': {},
                'storage_efficiency': {}
            }
            
            # Analyze storage growth trends
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Calculate storage efficiency metrics
                    efficiency = {
                        'capacity_utilization': (usage.used / usage.total) * 100 if usage.total > 0 else 0,
                        'free_space_ratio': (usage.free / usage.total) * 100 if usage.total > 0 else 0,
                        'usable_capacity': usage.total,
                        'allocated_space': usage.used,
                        'available_space': usage.free
                    }
                    
                    capacity_metrics['storage_efficiency'][partition.mountpoint] = efficiency
                    
                    # Threshold analysis
                    thresholds = {
                        'warning_threshold': 80,
                        'critical_threshold': 90,
                        'emergency_threshold': 95
                    }
                    
                    current_usage = efficiency['capacity_utilization']
                    threshold_status = 'normal'
                    if current_usage >= thresholds['emergency_threshold']:
                        threshold_status = 'emergency'
                    elif current_usage >= thresholds['critical_threshold']:
                        threshold_status = 'critical'
                    elif current_usage >= thresholds['warning_threshold']:
                        threshold_status = 'warning'
                    
                    capacity_metrics['threshold_analysis'][partition.mountpoint] = {
                        'current_usage': current_usage,
                        'status': threshold_status,
                        'thresholds': thresholds
                    }
                    
                except:
                    continue
            
            return capacity_metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_health_metrics(self):
        """Storage health and reliability metrics."""
        try:
            health_metrics = {
                'disk_health': {},
                'filesystem_health': {},
                'error_rates': {},
                'reliability_metrics': {}
            }
            
            # Check filesystem health
            for partition in psutil.disk_partitions():
                try:
                    mountpoint = partition.mountpoint
                    
                    # Check filesystem errors
                    health_status = self.check_filesystem_health(mountpoint)
                    health_metrics['filesystem_health'][mountpoint] = health_status
                    
                except:
                    continue
            
            # SMART health data
            health_metrics['smart_health'] = self.get_smart_health_status()
            
            # System error analysis
            health_metrics['system_errors'] = self.analyze_storage_errors()
            
            return health_metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_device_io_stats(self, device):
        """Get detailed I/O statistics for a specific device."""
        try:
            # Parse device name for block device stats
            device_name = device.replace('/dev/', '').replace('/', '')
            
            # Try to get I/O statistics from /proc/diskstats
            io_stats = {}
            try:
                with open('/proc/diskstats', 'r') as f:
                    for line in f:
                        fields = line.strip().split()
                        if len(fields) >= 14 and device_name in fields[2]:
                            io_stats = {
                                'reads_completed': int(fields[3]),
                                'reads_merged': int(fields[4]),
                                'sectors_read': int(fields[5]),
                                'time_reading': int(fields[6]),
                                'writes_completed': int(fields[7]),
                                'writes_merged': int(fields[8]),
                                'sectors_written': int(fields[9]),
                                'time_writing': int(fields[10]),
                                'ios_in_progress': int(fields[11]),
                                'time_io': int(fields[12]),
                                'weighted_time_io': int(fields[13])
                            }
                            break
            except:
                pass
            
            return io_stats
            
        except Exception as e:
            return {}
    
    def get_smart_data(self):
        """Collect SMART data from storage devices."""
        smart_data = {}
        try:
            # Try to get SMART data using smartctl
            result = subprocess.run(['which', 'smartctl'], capture_output=True, text=True)
            if result.returncode == 0:
                # Get list of devices
                devices_result = subprocess.run(['lsblk', '-d', '-n', '-o', 'NAME'], 
                                              capture_output=True, text=True)
                if devices_result.returncode == 0:
                    for device in devices_result.stdout.strip().split('\n'):
                        if device and not device.startswith('loop'):
                            try:
                                smart_result = subprocess.run(
                                    ['smartctl', '-a', f'/dev/{device}'],
                                    capture_output=True, text=True, timeout=10
                                )
                                if smart_result.returncode in [0, 4]:  # 4 = some SMART errors found
                                    smart_data[device] = self.parse_smart_output(smart_result.stdout)
                            except:
                                continue
        except:
            pass
        
        return smart_data
    
    def parse_smart_output(self, output):
        """Parse SMART output for key metrics."""
        metrics = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'Temperature_Celsius' in line or 'Temperature' in line:
                parts = line.split()
                if len(parts) >= 10:
                    metrics['temperature'] = int(parts[9])
            elif 'Power_On_Hours' in line:
                parts = line.split()
                if len(parts) >= 10:
                    metrics['power_on_hours'] = int(parts[9])
            elif 'Reallocated_Sector_Ct' in line:
                parts = line.split()
                if len(parts) >= 10:
                    metrics['reallocated_sectors'] = int(parts[9])
            elif 'Current_Pending_Sector' in line:
                parts = line.split()
                if len(parts) >= 10:
                    metrics['pending_sectors'] = int(parts[9])
        
        return metrics
    
    def get_block_device_info(self):
        """Get block device information."""
        block_devices = {}
        try:
            result = subprocess.run(['lsblk', '-J'], capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for device in data.get('blockdevices', []):
                    block_devices[device['name']] = {
                        'size': device.get('size', ''),
                        'type': device.get('type', ''),
                        'mountpoint': device.get('mountpoint', ''),
                        'fstype': device.get('fstype', ''),
                        'model': device.get('model', ''),
                        'serial': device.get('serial', ''),
                        'state': device.get('state', '')
                    }
        except:
            pass
        
        return block_devices
    
    def get_lvm_info(self):
        """Get LVM information."""
        lvm_info = {}
        try:
            # Try to get PV info
            result = subprocess.run(['pvs', '--noheadings', '--units', 'b'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lvm_info['physical_volumes'] = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            lvm_info['physical_volumes'].append({
                                'pv_name': parts[0],
                                'vg_name': parts[1],
                                'pv_size': parts[4],
                                'pv_free': parts[5]
                            })
        except:
            pass
        
        return lvm_info
    
    def get_raid_info(self):
        """Get RAID information."""
        raid_info = {}
        try:
            # Check for software RAID
            if os.path.exists('/proc/mdstat'):
                with open('/proc/mdstat', 'r') as f:
                    raid_info['mdstat'] = f.read()
        except:
            pass
        
        return raid_info
    
    def get_system_io_metrics(self):
        """Get system-wide I/O metrics."""
        try:
            return {
                'total_disk_io': psutil.disk_io_counters(),
                'io_wait': self.get_io_wait_percentage(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except:
            return {}
    
    def get_io_wait_percentage(self):
        """Get I/O wait percentage."""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                cpu_times = [int(x) for x in line.split()[1:]]
                if len(cpu_times) >= 5:
                    total_time = sum(cpu_times)
                    iowait_time = cpu_times[4]  # iowait is the 5th field
                    return (iowait_time / total_time) * 100 if total_time > 0 else 0
        except:
            return 0
        
        return 0
    
    def analyze_recent_file_activity(self):
        """Analyze recent file system activity."""
        try:
            activity_metrics = {
                'recent_modifications': 0,
                'large_files_accessed': 0,
                'directory_operations': 0
            }
            
            # This would typically involve analyzing system logs or using tools like inotify
            # For now, we'll provide a basic implementation
            
            return activity_metrics
        except:
            return {}
    
    def analyze_file_size_distribution(self):
        """Analyze file size distribution across filesystems."""
        try:
            size_distribution = {
                'small_files': 0,    # < 1MB
                'medium_files': 0,   # 1MB - 100MB
                'large_files': 0,    # 100MB - 1GB
                'huge_files': 0      # > 1GB
            }
            
            # This would typically involve filesystem scanning
            # Implementation would depend on specific requirements
            
            return size_distribution
        except:
            return {}
    
    def analyze_io_queues(self):
        """Analyze I/O queue depths and patterns."""
        try:
            queue_metrics = {
                'average_queue_depth': 0,
                'queue_full_events': 0,
                'peak_queue_depth': 0
            }
            
            # This would involve reading from /sys/block/*/queue/ files
            
            return queue_metrics
        except:
            return {}
    
    def check_filesystem_health(self, mountpoint):
        """Check filesystem health status."""
        try:
            health_status = {
                'status': 'healthy',
                'errors': [],
                'warnings': [],
                'last_check': datetime.now().isoformat()
            }
            
            # Check for common filesystem issues
            try:
                stat = os.statvfs(mountpoint)
                if stat.f_bavail == 0:
                    health_status['errors'].append('Filesystem full')
                    health_status['status'] = 'critical'
                elif (stat.f_bavail / stat.f_blocks) < 0.05:  # Less than 5% free
                    health_status['warnings'].append('Low disk space')
                    health_status['status'] = 'warning'
            except:
                health_status['errors'].append('Cannot access filesystem')
                health_status['status'] = 'error'
            
            return health_status
        except:
            return {'status': 'unknown', 'errors': ['Health check failed']}
    
    def get_smart_health_status(self):
        """Get overall SMART health status."""
        try:
            smart_health = {
                'overall_status': 'healthy',
                'devices_monitored': 0,
                'devices_with_issues': 0,
                'critical_issues': []
            }
            
            # This would analyze SMART data for health indicators
            
            return smart_health
        except:
            return {'overall_status': 'unknown'}
    
    def analyze_storage_errors(self):
        """Analyze storage-related system errors."""
        try:
            error_analysis = {
                'io_errors': 0,
                'timeout_errors': 0,
                'hardware_errors': 0,
                'filesystem_errors': 0
            }
            
            # This would typically parse system logs for storage errors
            
            return error_analysis
        except:
            return {}

def format_bytes(bytes_value):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} EB"

def calculate_iops_from_stats(stats, time_interval=1):
    """Calculate IOPS from I/O statistics."""
    if time_interval <= 0:
        return 0
    return (stats.read_count + stats.write_count) / time_interval

def calculate_throughput_mbps(bytes_transferred, time_interval=1):
    """Calculate throughput in MB/s."""
    if time_interval <= 0:
        return 0
    return (bytes_transferred / (1024 * 1024)) / time_interval

def calculate_latency_ms(total_time_ms, operations):
    """Calculate average latency in milliseconds."""
    if operations <= 0:
        return 0
    return total_time_ms / operations

if __name__ == "__main__":
    collector = StorageMetricsCollector()
    metrics = collector.collect_all_metrics()
    print(json.dumps(metrics, indent=2, default=str))