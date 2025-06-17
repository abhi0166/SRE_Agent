"""
Premium monitoring dashboard with advanced data visualization.
Enterprise-grade UI/UX inspired by successful revenue-generating applications.
"""

import os
import requests
import psutil
import json
from flask import Flask, render_template_string, jsonify
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

def get_enhanced_system_metrics():
    """Get comprehensive system metrics with trends."""
    try:
        # Current metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Process information
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['cpu_percent'] > 0:
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Top 5 processes by CPU
        top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
        
        # Temperature (if available)
        temperature = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                temperature = list(temps.values())[0][0].current if temps else None
        except:
            pass
        
        return {
            'system': {
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'cached': getattr(memory, 'cached', 0)
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'temperature': temperature,
                'processes': top_processes
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': str(e)}

def get_alert_analytics():
    """Get advanced alert analytics."""
    try:
        response = requests.get('http://localhost:5000/api/alerts?limit=50', timeout=5)
        if response.status_code == 200:
            alerts = response.json().get('alerts', [])
            
            # Analytics calculations
            analytics = {
                'total_count': len(alerts),
                'severity_distribution': defaultdict(int),
                'hourly_distribution': defaultdict(int),
                'recent_trends': [],
                'top_alert_types': defaultdict(int),
                'resolution_rate': 0
            }
            
            for alert in alerts:
                # Severity distribution
                analytics['severity_distribution'][alert.get('severity', 'unknown')] += 1
                
                # Alert type distribution
                analytics['top_alert_types'][alert.get('alertname', 'unknown')] += 1
                
                # Hourly distribution
                try:
                    timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                    hour = timestamp.hour
                    analytics['hourly_distribution'][hour] += 1
                except:
                    pass
            
            # Convert to lists for charts
            analytics['severity_distribution'] = dict(analytics['severity_distribution'])
            analytics['hourly_distribution'] = dict(analytics['hourly_distribution'])
            analytics['top_alert_types'] = dict(sorted(analytics['top_alert_types'].items(), 
                                                      key=lambda x: x[1], reverse=True)[:10])
            
            return analytics
        else:
            return {}
    except Exception as e:
        return {}

def format_bytes(bytes_value):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

@app.route('/')
def premium_dashboard():
    """Premium dashboard with advanced analytics."""
    system_metrics = get_enhanced_system_metrics()
    alert_analytics = get_alert_analytics()
    
    # Get stored alerts
    try:
        response = requests.get('http://localhost:5000/api/alerts?limit=15', timeout=5)
        recent_alerts = response.json().get('alerts', []) if response.status_code == 200 else []
    except:
        recent_alerts = []
    
    # Get database stats
    try:
        response = requests.get('http://localhost:5000/api/database/status', timeout=5)
        database_stats = response.json() if response.status_code == 200 else {}
    except:
        database_stats = {}
    
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Analytics Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --accent: #06b6d4;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            
            /* Dark theme */
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --border-color: #334155;
            
            /* Gradients */
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            
            /* Spacing */
            --space-xs: 0.25rem;
            --space-sm: 0.5rem;
            --space-md: 1rem;
            --space-lg: 1.5rem;
            --space-xl: 2rem;
            --space-2xl: 3rem;
            
            /* Border radius */
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
            
            /* Shadows */
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .dashboard-container {
            max-width: 1600px;
            margin: 0 auto;
            padding: var(--space-lg);
        }
        
        /* Header */
        .header {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-xl);
            padding: var(--space-xl);
            margin-bottom: var(--space-xl);
            backdrop-filter: blur(20px);
            box-shadow: var(--shadow-lg);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: var(--space-lg);
        }
        
        .header-title {
            display: flex;
            align-items: center;
            gap: var(--space-md);
        }
        
        .header-title h1 {
            font-size: 2rem;
            font-weight: 800;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .system-status {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-sm) var(--space-lg);
            background: var(--gradient-success);
            border-radius: var(--radius-lg);
            color: white;
            font-weight: 600;
            font-size: 0.875rem;
            box-shadow: var(--shadow-md);
        }
        
        /* Grid Layouts */
        .grid {
            display: grid;
            gap: var(--space-xl);
            margin-bottom: var(--space-xl);
        }
        
        .grid-responsive {
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .grid-2 {
            grid-template-columns: 2fr 1fr;
        }
        
        .grid-3 {
            grid-template-columns: repeat(3, 1fr);
        }
        
        .grid-4 {
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }
        
        /* Cards */
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-xl);
            padding: var(--space-xl);
            box-shadow: var(--shadow-lg);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(20px);
        }
        
        .card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
            border-color: var(--primary-light);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-lg);
        }
        
        .card-title {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            font-size: 1.125rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        .card-icon {
            width: 1.5rem;
            height: 1.5rem;
            color: var(--primary-light);
        }
        
        /* Metrics */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: var(--space-lg);
        }
        
        .metric {
            text-align: center;
            padding: var(--space-lg);
            background: var(--bg-tertiary);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }
        
        .metric:hover {
            background: var(--bg-secondary);
            transform: scale(1.02);
        }
        
        .metric-value {
            font-size: 1.75rem;
            font-weight: 800;
            margin-bottom: var(--space-xs);
            color: var(--text-primary);
        }
        
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            font-weight: 600;
        }
        
        /* Progress Bars */
        .progress-container {
            margin-top: var(--space-sm);
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-primary);
            border-radius: var(--radius-sm);
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: var(--radius-sm);
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .progress-success { background: var(--gradient-success); }
        .progress-warning { background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%); }
        .progress-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
        
        /* Charts Container */
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: var(--space-lg);
        }
        
        .chart-small {
            height: 200px;
        }
        
        /* Alerts */
        .alert-item {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            margin-bottom: var(--space-md);
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        
        .alert-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--text-muted);
        }
        
        .alert-item:hover {
            transform: translateX(4px);
            background: var(--bg-secondary);
        }
        
        .alert-critical::before { background: var(--danger); }
        .alert-warning::before { background: var(--warning); }
        .alert-info::before { background: var(--info); }
        
        .alert-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: var(--space-sm);
        }
        
        .alert-title {
            font-weight: 700;
            color: var(--text-primary);
            font-size: 1rem;
        }
        
        .alert-time {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 500;
        }
        
        .alert-severity {
            display: inline-block;
            padding: var(--space-xs) var(--space-sm);
            border-radius: var(--radius-sm);
            font-size: 0.625rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: var(--space-sm);
        }
        
        .severity-critical {
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .severity-warning {
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        
        .severity-info {
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        
        /* Process List */
        .process-list {
            max-height: 250px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border-color) transparent;
        }
        
        .process-item {
            display: flex;
            justify-content: between;
            align-items: center;
            padding: var(--space-sm) 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .process-item:last-child {
            border-bottom: none;
        }
        
        .process-name {
            flex: 1;
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .process-cpu {
            font-size: 0.75rem;
            color: var(--primary-light);
            font-weight: 600;
            min-width: 60px;
            text-align: right;
        }
        
        /* Empty States */
        .empty-state {
            text-align: center;
            padding: var(--space-2xl);
            color: var(--text-muted);
        }
        
        .empty-state i {
            font-size: 3rem;
            margin-bottom: var(--space-lg);
            opacity: 0.5;
        }
        
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: var(--space-lg);
        }
        
        .stat-card {
            background: var(--gradient-primary);
            color: white;
            padding: var(--space-xl);
            border-radius: var(--radius-xl);
            text-align: center;
            box-shadow: var(--shadow-lg);
            transition: transform 0.2s ease;
        }
        
        .stat-card:hover {
            transform: scale(1.05);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: var(--space-xs);
        }
        
        .stat-label {
            font-size: 0.875rem;
            opacity: 0.9;
            font-weight: 500;
        }
        
        /* Responsive Design */
        @media (max-width: 1024px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
            
            .dashboard-container {
                padding: var(--space-md);
            }
        }
        
        @media (max-width: 768px) {
            .header {
                padding: var(--space-lg);
            }
            
            .header-content {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .header-title h1 {
                font-size: 1.5rem;
            }
            
            .grid-4 {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .metric-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 480px) {
            .dashboard-container {
                padding: var(--space-sm);
            }
            
            .card {
                padding: var(--space-lg);
            }
            
            .grid-4 {
                grid-template-columns: 1fr;
            }
            
            .metric-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <div class="header">
            <div class="header-content">
                <div class="header-title">
                    <i class="fas fa-chart-line card-icon"></i>
                    <h1>System Analytics Pro</h1>
                </div>
                <div class="system-status">
                    <i class="fas fa-circle"></i>
                    Real-time Monitoring Active
                </div>
            </div>
        </div>

        <!-- Key Performance Indicators -->
        {% if system_metrics.system %}
        <div class="grid grid-4">
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_metrics.system.cpu.percent) }}%</div>
                    <div class="metric-label">CPU Usage</div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill {{ 'progress-danger' if system_metrics.system.cpu.percent > 80 else 'progress-warning' if system_metrics.system.cpu.percent > 60 else 'progress-success' }}" 
                                 style="width: {{ system_metrics.system.cpu.percent }}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_metrics.system.memory.percent) }}%</div>
                    <div class="metric-label">Memory Usage</div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill {{ 'progress-danger' if system_metrics.system.memory.percent > 80 else 'progress-warning' if system_metrics.system.memory.percent > 60 else 'progress-success' }}" 
                                 style="width: {{ system_metrics.system.memory.percent }}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_metrics.system.disk.percent) }}%</div>
                    <div class="metric-label">Disk Usage</div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill {{ 'progress-danger' if system_metrics.system.disk.percent > 80 else 'progress-warning' if system_metrics.system.disk.percent > 60 else 'progress-success' }}" 
                                 style="width: {{ system_metrics.system.disk.percent }}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ system_metrics.system.processes|length }}</div>
                    <div class="metric-label">Active Processes</div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Database Analytics -->
        {% if database_stats.connected %}
        <div class="card" style="margin-bottom: var(--space-xl);">
            <div class="card-header">
                <div class="card-title">
                    <i class="fas fa-database card-icon"></i>
                    Alert Analytics
                </div>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{{ database_stats.stats.total_alerts }}</div>
                    <div class="stat-label">Total Alerts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ database_stats.stats.recent_24h }}</div>
                    <div class="stat-label">Last 24 Hours</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ database_stats.stats.by_severity.get('critical', 0) }}</div>
                    <div class="stat-label">Critical</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ database_stats.stats.by_severity.get('warning', 0) }}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ database_stats.stats.jira_tickets }}</div>
                    <div class="stat-label">JIRA Tickets</div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Main Dashboard Grid -->
        <div class="grid grid-2">
            <!-- Recent Alerts with Visualization -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <i class="fas fa-exclamation-triangle card-icon"></i>
                        Recent Alerts
                    </div>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Live Updates</span>
                </div>
                
                {% if alert_analytics.severity_distribution %}
                <div class="chart-container chart-small">
                    <canvas id="alertsChart"></canvas>
                </div>
                {% endif %}
                
                {% if recent_alerts %}
                    <div style="max-height: 300px; overflow-y: auto; margin-top: var(--space-lg);">
                        {% for alert in recent_alerts[:8] %}
                        <div class="alert-item alert-{{ alert.severity }}">
                            <div class="alert-header">
                                <div class="alert-title">{{ alert.alertname }}</div>
                                <div class="alert-time">{{ alert.get('formatted_time', 'Unknown') }}</div>
                            </div>
                            <div class="alert-severity severity-{{ alert.severity }}">{{ alert.severity }}</div>
                            <div style="font-size: 0.875rem; color: var(--text-secondary); margin-top: var(--space-sm);">
                                {{ alert.annotations.get('description', alert.annotations.get('summary', 'No description available'))[:100] }}{% if alert.annotations.get('description', '')|length > 100 %}...{% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="empty-state">
                        <i class="fas fa-shield-alt"></i>
                        <p>No alerts detected</p>
                        <small>System operating normally</small>
                    </div>
                {% endif %}
            </div>

            <!-- System Performance -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <i class="fas fa-tachometer-alt card-icon"></i>
                        System Performance
                    </div>
                </div>
                
                {% if system_metrics.system %}
                <div class="chart-container chart-small">
                    <canvas id="performanceChart"></canvas>
                </div>
                
                <!-- Top Processes -->
                <div style="margin-top: var(--space-lg);">
                    <h4 style="margin-bottom: var(--space-md); color: var(--text-secondary); font-size: 0.875rem; font-weight: 600;">Top Processes</h4>
                    <div class="process-list">
                        {% for proc in system_metrics.system.processes %}
                        <div class="process-item">
                            <div class="process-name">{{ proc.name[:20] }}{% if proc.name|length > 20 %}...{% endif %}</div>
                            <div class="process-cpu">{{ "%.1f"|format(proc.cpu_percent) }}%</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- System Details -->
        {% if system_metrics.system %}
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <i class="fas fa-server card-icon"></i>
                    System Information
                </div>
            </div>
            
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value">{{ system_metrics.system.cpu.cores }}</div>
                    <div class="metric-label">CPU Cores</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ format_bytes(system_metrics.system.memory.total) }}</div>
                    <div class="metric-label">Total RAM</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ format_bytes(system_metrics.system.disk.total) }}</div>
                    <div class="metric-label">Storage</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ format_bytes(system_metrics.system.network.bytes_recv) }}</div>
                    <div class="metric-label">Network RX</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ format_bytes(system_metrics.system.network.bytes_sent) }}</div>
                    <div class="metric-label">Network TX</div>
                </div>
                {% if system_metrics.system.temperature %}
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_metrics.system.temperature) }}°C</div>
                    <div class="metric-label">Temperature</div>
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        // Chart.js Configuration
        Chart.defaults.color = '#cbd5e1';
        Chart.defaults.borderColor = '#334155';
        Chart.defaults.backgroundColor = 'rgba(99, 102, 241, 0.1)';

        // Alerts Distribution Chart
        {% if alert_analytics.severity_distribution %}
        const alertsCtx = document.getElementById('alertsChart').getContext('2d');
        new Chart(alertsCtx, {
            type: 'doughnut',
            data: {
                labels: {{ alert_analytics.severity_distribution.keys() | list | tojson }},
                datasets: [{
                    data: {{ alert_analytics.severity_distribution.values() | list | tojson }},
                    backgroundColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#3b82f6',
                        '#10b981'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
        {% endif %}

        // Performance Chart
        {% if system_metrics.system %}
        const perfCtx = document.getElementById('performanceChart').getContext('2d');
        new Chart(perfCtx, {
            type: 'bar',
            data: {
                labels: ['CPU', 'Memory', 'Disk'],
                datasets: [{
                    label: 'Usage %',
                    data: [
                        {{ system_metrics.system.cpu.percent }},
                        {{ system_metrics.system.memory.percent }},
                        {{ system_metrics.system.disk.percent }}
                    ],
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(6, 182, 212, 0.8)'
                    ],
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#334155'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        {% endif %}

        // Auto-refresh functionality
        setInterval(() => {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    // Update performance chart
                    if (window.performanceChart) {
                        performanceChart.data.datasets[0].data = [data.cpu, data.memory, data.disk];
                        performanceChart.update('none');
                    }
                })
                .catch(console.error);
        }, 10000);

        // Smooth page reload every 30 seconds
        setTimeout(() => {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>
    """
    
    return render_template_string(dashboard_html, 
                                system_metrics=system_metrics,
                                alert_analytics=alert_analytics,
                                recent_alerts=recent_alerts,
                                database_stats=database_stats,
                                format_bytes=format_bytes)

@app.route('/api/metrics')
def real_time_metrics():
    """Real-time metrics endpoint for live updates."""
    try:
        return jsonify({
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Premium Analytics Dashboard on http://localhost:3000")
    print("Enterprise-grade monitoring with advanced data visualization")
    app.run(host='0.0.0.0', port=3000, debug=False)