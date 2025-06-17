#!/usr/bin/env python3
"""
Simple monitoring dashboard to display system status and recent alerts.
"""

import os
import json
import time
import psutil
import requests
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Store recent alerts in memory for demonstration
recent_alerts = []
max_alerts = 50

def get_system_status():
    """Get current system status."""
    try:
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk usage for main partitions
        disk_info = []
        for partition in psutil.disk_partitions():
            if partition.mountpoint in ['/home/runner/workspace', '/', '/tmp']:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        'mountpoint': partition.mountpoint,
                        'device': partition.device,
                        'usage_percent': round((usage.used / usage.total) * 100, 1),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'total_gb': round(usage.total / (1024**3), 2)
                    })
                except (PermissionError, FileNotFoundError):
                    continue
        
        # Load average
        try:
            load_avg = os.getloadavg()
        except AttributeError:
            load_avg = (0, 0, 0)
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'load_avg': [round(x, 2) for x in load_avg],
            'disk_info': disk_info
        }
    except Exception as e:
        return {'error': str(e)}

def check_webhook_status():
    """Check if webhook server is responsive."""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {'status': 'error', 'message': f'HTTP {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def dashboard():
    """Main dashboard page."""
    system_status = get_system_status()
    webhook_status = check_webhook_status()
    
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Disk Monitoring Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .status-card h3 { margin-top: 0; color: #2c3e50; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-value { font-weight: bold; }
        .status-ok { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
        .alerts-section { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .alert-item { border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; background: #ecf0f1; }
        .alert-warning { border-left-color: #f39c12; }
        .alert-critical { border-left-color: #e74c3c; }
        .endpoints { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .endpoint { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ Disk Monitoring System Dashboard</h1>
            <p>Real-time system monitoring with automated JIRA ticket creation</p>
            <p><strong>Last Updated:</strong> {{ system_status.timestamp }}</p>
        </div>
        
        <div class="endpoints">
            <h3>🔗 Available Endpoints</h3>
            <div class="endpoint">Webhook: <a href="http://localhost:5000/webhook/alert" target="_blank">http://localhost:5000/webhook/alert</a></div>
            <div class="endpoint">Health Check: <a href="http://localhost:5000/health" target="_blank">http://localhost:5000/health</a></div>
            <div class="endpoint">Test Alerts: <a href="http://localhost:5000/test" target="_blank">http://localhost:5000/test</a></div>
            <div class="endpoint">Dashboard API: <a href="/api/status" target="_blank">/api/status</a></div>
        </div>

        <div class="status-grid">
            <div class="status-card">
                <h3>📊 System Resources</h3>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span class="metric-value {% if system_status.cpu_percent > 80 %}status-critical{% elif system_status.cpu_percent > 60 %}status-warning{% else %}status-ok{% endif %}">
                        {{ system_status.cpu_percent }}%
                    </span>
                </div>
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span class="metric-value {% if system_status.memory_percent > 80 %}status-critical{% elif system_status.memory_percent > 60 %}status-warning{% else %}status-ok{% endif %}">
                        {{ system_status.memory_percent }}% ({{ system_status.memory_used_gb }}GB/{{ system_status.memory_total_gb }}GB)
                    </span>
                </div>
                <div class="metric">
                    <span>Load Average:</span>
                    <span class="metric-value {% if system_status.load_avg[0] > 4 %}status-warning{% else %}status-ok{% endif %}">
                        {{ system_status.load_avg[0] }}, {{ system_status.load_avg[1] }}, {{ system_status.load_avg[2] }}
                    </span>
                </div>
            </div>

            <div class="status-card">
                <h3>💾 Disk Usage</h3>
                {% for disk in system_status.disk_info %}
                <div class="metric">
                    <span>{{ disk.mountpoint }}:</span>
                    <span class="metric-value {% if disk.usage_percent > 90 %}status-critical{% elif disk.usage_percent > 80 %}status-warning{% else %}status-ok{% endif %}">
                        {{ disk.usage_percent }}% ({{ disk.used_gb }}GB/{{ disk.total_gb }}GB)
                    </span>
                </div>
                {% endfor %}
            </div>

            <div class="status-card">
                <h3>🔗 Webhook Server</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value {% if webhook_status.status == 'healthy' %}status-ok{% else %}status-critical{% endif %}">
                        {{ webhook_status.status|title }}
                    </span>
                </div>
                <div class="metric">
                    <span>JIRA Configured:</span>
                    <span class="metric-value {% if webhook_status.jira_configured %}status-ok{% else %}status-warning{% endif %}">
                        {{ 'Yes' if webhook_status.jira_configured else 'No' }}
                    </span>
                </div>
                {% if webhook_status.timestamp %}
                <div class="metric">
                    <span>Last Health Check:</span>
                    <span class="metric-value">{{ webhook_status.timestamp.split('T')[1].split('.')[0] }}</span>
                </div>
                {% endif %}
            </div>
        </div>

        <div class="alerts-section">
            <h3>🚨 Monitoring Commands</h3>
            <p>Use these commands to test the monitoring system:</p>
            <div class="endpoint"><strong>Test Alert:</strong> python monitoring/disk_monitor.py --test</div>
            <div class="endpoint"><strong>Check Once:</strong> python monitoring/system_monitor.py --once</div>
            <div class="endpoint"><strong>Run Test Scenarios:</strong> python monitoring/system_monitor.py --test</div>
            <div class="endpoint"><strong>Continuous Monitoring:</strong> python monitoring/system_monitor.py</div>
            
            <h4>💡 Setup JIRA Integration</h4>
            <p>To enable automatic JIRA ticket creation, configure these environment variables in <code>.env</code>:</p>
            <ul>
                <li><strong>JIRA_URL:</strong> Your JIRA instance URL</li>
                <li><strong>JIRA_USERNAME:</strong> Your JIRA username/email</li>
                <li><strong>JIRA_API_TOKEN:</strong> JIRA API token</li>
                <li><strong>JIRA_PROJECT:</strong> Project key (default: DCOPS)</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(dashboard_html, 
                                system_status=system_status, 
                                webhook_status=webhook_status)

@app.route('/api/status')
def api_status():
    """API endpoint for system status."""
    return jsonify({
        'system': get_system_status(),
        'webhook': check_webhook_status(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting Monitoring Dashboard on http://localhost:3000")
    print("Webhook Server should be running on http://localhost:5000")
    app.run(host='0.0.0.0', port=3000, debug=False)