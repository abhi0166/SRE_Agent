"""
Professional-grade monitoring dashboard with modern UI/UX design.
Inspired by successful apps like Netflix, Snapchat, and modern SaaS platforms.
"""

import os
import requests
import psutil
from flask import Flask, render_template_string, jsonify
from datetime import datetime, timedelta
import json

app = Flask(__name__)

def get_system_status():
    """Get comprehensive system status with enhanced metrics."""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Network stats
        network = psutil.net_io_counters()
        
        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
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
            'uptime': str(uptime).split('.')[0],
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': str(e)}

def check_webhook_status():
    """Enhanced webhook status check."""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            data['response_time'] = response.elapsed.total_seconds()
            return data
        else:
            return {'status': 'error', 'message': f'HTTP {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': str(e)}

def get_stored_alerts():
    """Get stored alerts with enhanced processing."""
    try:
        response = requests.get('http://localhost:5000/api/alerts?limit=20', timeout=5)
        if response.status_code == 200:
            alerts = response.json().get('alerts', [])
            # Process alerts for better display
            for alert in alerts:
                if 'timestamp' in alert:
                    try:
                        alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                        alert['time_ago'] = get_time_ago(alert_time)
                        alert['formatted_time'] = alert_time.strftime('%H:%M:%S')
                    except:
                        alert['time_ago'] = 'Unknown'
                        alert['formatted_time'] = 'Unknown'
            return alerts
        else:
            return []
    except requests.exceptions.RequestException as e:
        return []

def get_database_stats():
    """Get enhanced database statistics."""
    try:
        response = requests.get('http://localhost:5000/api/database/status', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {'connected': False}
    except requests.exceptions.RequestException as e:
        return {'connected': False}

def get_time_ago(timestamp):
    """Convert timestamp to human-readable time ago."""
    now = datetime.now()
    if timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=None)
    
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"

def format_bytes(bytes_value):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

@app.route('/')
def dashboard():
    """Modern monitoring dashboard with professional UI/UX."""
    system_status = get_system_status()
    webhook_status = check_webhook_status()
    stored_alerts = get_stored_alerts()
    database_stats = get_database_stats()
    
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Monitor Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --dark: #1f2937;
            --light: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --border-radius: 12px;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--gray-800);
            line-height: 1.6;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: var(--border-radius);
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: var(--shadow);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        
        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-title h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--gray-900);
            margin: 0;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .status-online {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        
        .status-offline {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }
        
        .grid {
            display: grid;
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .grid-2 {
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .grid-3 {
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }
        
        .grid-4 {
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: var(--border-radius);
            padding: 24px;
            box-shadow: var(--shadow);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        
        .card-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 18px;
            font-weight: 600;
            color: var(--gray-900);
        }
        
        .card-icon {
            width: 24px;
            height: 24px;
            color: var(--primary);
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 16px;
        }
        
        .metric {
            text-align: center;
            padding: 16px;
            background: var(--gray-50);
            border-radius: 8px;
            border: 1px solid var(--gray-200);
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
            color: var(--gray-900);
        }
        
        .metric-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--gray-500);
            font-weight: 500;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--gray-200);
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .progress-success { background: var(--success); }
        .progress-warning { background: var(--warning); }
        .progress-danger { background: var(--danger); }
        
        .alert-item {
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 4px solid var(--gray-300);
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }
        
        .alert-item:hover {
            transform: translateX(4px);
            box-shadow: var(--shadow);
        }
        
        .alert-critical { border-left-color: var(--danger); }
        .alert-warning { border-left-color: var(--warning); }
        .alert-info { border-left-color: var(--info); }
        
        .alert-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        
        .alert-title {
            font-weight: 600;
            color: var(--gray-900);
            font-size: 16px;
        }
        
        .alert-time {
            font-size: 12px;
            color: var(--gray-500);
            font-weight: 500;
        }
        
        .alert-severity {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .severity-critical {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }
        
        .severity-warning {
            background: rgba(245, 158, 11, 0.1);
            color: var(--warning);
        }
        
        .severity-info {
            background: rgba(59, 130, 246, 0.1);
            color: var(--info);
        }
        
        .alert-description {
            color: var(--gray-600);
            font-size: 14px;
            line-height: 1.5;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px 16px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border-radius: 12px;
            box-shadow: var(--shadow);
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        
        .stat-label {
            font-size: 13px;
            opacity: 0.9;
            font-weight: 500;
        }
        
        .empty-state {
            text-align: center;
            padding: 48px 24px;
            color: var(--gray-500);
        }
        
        .empty-state i {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
        
        .refresh-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--primary);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: var(--shadow);
            display: none;
            align-items: center;
            gap: 8px;
        }
        
        .refresh-indicator.show {
            display: flex;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .spinning {
            animation: spin 1s linear infinite;
        }
        
        .endpoint-list {
            list-style: none;
            padding: 0;
        }
        
        .endpoint-item {
            background: var(--gray-50);
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid var(--gray-200);
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
        }
        
        .endpoint-item a {
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }
        
        .endpoint-item a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            .dashboard-container {
                padding: 16px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header-content {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .grid-4 {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
            
            .metric-grid {
                grid-template-columns: 1fr 1fr;
            }
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
                    <h1>System Monitor Pro</h1>
                </div>
                <div class="status-indicator {{ 'status-online' if webhook_status.status == 'healthy' else 'status-offline' }}">
                    <i class="fas fa-circle"></i>
                    {{ 'System Online' if webhook_status.status == 'healthy' else 'System Offline' }}
                </div>
            </div>
        </div>

        <!-- Key Metrics -->
        {% if system_status and not system_status.get('error') %}
        <div class="grid grid-4">
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_status.cpu.percent) }}%</div>
                    <div class="metric-label">CPU Usage</div>
                    <div class="progress-bar">
                        <div class="progress-fill {{ 'progress-danger' if system_status.cpu.percent > 80 else 'progress-warning' if system_status.cpu.percent > 60 else 'progress-success' }}" 
                             style="width: {{ system_status.cpu.percent }}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_status.memory.percent) }}%</div>
                    <div class="metric-label">Memory Usage</div>
                    <div class="progress-bar">
                        <div class="progress-fill {{ 'progress-danger' if system_status.memory.percent > 80 else 'progress-warning' if system_status.memory.percent > 60 else 'progress-success' }}" 
                             style="width: {{ system_status.memory.percent }}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(system_status.disk.percent) }}%</div>
                    <div class="metric-label">Disk Usage</div>
                    <div class="progress-bar">
                        <div class="progress-fill {{ 'progress-danger' if system_status.disk.percent > 80 else 'progress-warning' if system_status.disk.percent > 60 else 'progress-success' }}" 
                             style="width: {{ system_status.disk.percent }}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="metric">
                    <div class="metric-value">{{ system_status.uptime }}</div>
                    <div class="metric-label">System Uptime</div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Database Statistics -->
        {% if database_stats.connected %}
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-header">
                <div class="card-title">
                    <i class="fas fa-database card-icon"></i>
                    Database Analytics
                </div>
            </div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{{ database_stats.stats.total_alerts }}</div>
                    <div class="stat-label">Total Alerts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ database_stats.stats.recent_24h }}</div>
                    <div class="stat-label">Last 24h</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ database_stats.stats.by_severity.get('critical', 0) }}</div>
                    <div class="stat-label">Critical</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ database_stats.stats.by_severity.get('warning', 0) }}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ database_stats.stats.jira_tickets }}</div>
                    <div class="stat-label">JIRA Tickets</div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Main Content Grid -->
        <div class="grid grid-2">
            <!-- Recent Alerts -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <i class="fas fa-exclamation-triangle card-icon"></i>
                        Recent Alerts
                    </div>
                    <span style="font-size: 12px; color: var(--gray-500);">Live Updates</span>
                </div>
                
                {% if stored_alerts %}
                    <div style="max-height: 400px; overflow-y: auto;">
                        {% for alert in stored_alerts[:10] %}
                        <div class="alert-item alert-{{ alert.severity }}">
                            <div class="alert-header">
                                <div class="alert-title">{{ alert.alertname }}</div>
                                <div class="alert-time">{{ alert.get('time_ago', 'Unknown') }}</div>
                            </div>
                            <div class="alert-severity severity-{{ alert.severity }}">{{ alert.severity }}</div>
                            <div class="alert-description">
                                {{ alert.annotations.get('description', alert.annotations.get('summary', 'No description available')) }}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="empty-state">
                        <i class="fas fa-shield-alt"></i>
                        <p>No alerts found</p>
                        <small>Your system is running smoothly</small>
                    </div>
                {% endif %}
            </div>

            <!-- System Details -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <i class="fas fa-server card-icon"></i>
                        System Details
                    </div>
                </div>
                
                {% if system_status and not system_status.get('error') %}
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{{ system_status.cpu.cores }}</div>
                        <div class="metric-label">CPU Cores</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ format_bytes(system_status.memory.total) }}</div>
                        <div class="metric-label">Total RAM</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ format_bytes(system_status.disk.total) }}</div>
                        <div class="metric-label">Total Storage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{{ format_bytes(system_status.network.bytes_recv) }}</div>
                        <div class="metric-label">Data Received</div>
                    </div>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- API Endpoints -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <i class="fas fa-link card-icon"></i>
                    API Endpoints
                </div>
            </div>
            
            <ul class="endpoint-list">
                <li class="endpoint-item">
                    <strong>Webhook:</strong> 
                    <a href="http://localhost:5000/webhook/alert" target="_blank">http://localhost:5000/webhook/alert</a>
                </li>
                <li class="endpoint-item">
                    <strong>Health Check:</strong> 
                    <a href="http://localhost:5000/health" target="_blank">http://localhost:5000/health</a>
                </li>
                <li class="endpoint-item">
                    <strong>Test Alerts:</strong> 
                    <a href="http://localhost:5000/test" target="_blank">http://localhost:5000/test</a>
                </li>
                <li class="endpoint-item">
                    <strong>Dashboard API:</strong> 
                    <a href="/api/status" target="_blank">/api/status</a>
                </li>
            </ul>
        </div>
    </div>

    <!-- Refresh Indicator -->
    <div class="refresh-indicator" id="refreshIndicator">
        <i class="fas fa-sync-alt spinning"></i>
        Updating...
    </div>

    <script>
        // Auto-refresh functionality
        let refreshInterval;
        
        function showRefreshIndicator() {
            document.getElementById('refreshIndicator').classList.add('show');
        }
        
        function hideRefreshIndicator() {
            document.getElementById('refreshIndicator').classList.remove('show');
        }
        
        function refreshData() {
            showRefreshIndicator();
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
        
        // Auto-refresh every 30 seconds
        refreshInterval = setInterval(refreshData, 30000);
        
        // Progressive enhancement for real-time updates
        if (window.fetch) {
            // Implement AJAX updates here for smoother experience
            console.log('Enhanced refresh capabilities available');
        }
        
        // Add smooth scroll behavior
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // Add hover effects and micro-interactions
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-4px)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    </script>
</body>
</html>
    """
    
    return render_template_string(dashboard_html, 
                                system_status=system_status, 
                                webhook_status=webhook_status,
                                stored_alerts=stored_alerts,
                                database_stats=database_stats,
                                format_bytes=format_bytes)

@app.route('/api/status')
def api_status():
    """Enhanced API endpoint for system status."""
    return jsonify({
        'system': get_system_status(),
        'webhook': check_webhook_status(),
        'alerts': get_stored_alerts(),
        'database': get_database_stats(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/metrics')
def api_metrics():
    """Real-time metrics endpoint for AJAX updates."""
    return jsonify({
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'disk': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting Enhanced Monitoring Dashboard on http://localhost:3000")
    print("Professional UI/UX with modern design patterns")
    app.run(host='0.0.0.0', port=3000, debug=False)