#!/usr/bin/env python3
"""
Flask webhook server for receiving Prometheus alerts and creating JIRA tickets.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from jira_client import JiraClient
from database.sqlite_store import SQLiteAlertStore
from slack_integration import send_alert_to_slack, get_slack_notifier

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize JIRA client and database
jira_client = JiraClient()
alert_store = SQLiteAlertStore()

def format_alert_for_jira(alert_data):
    """
    Format Prometheus alert data into JIRA ticket format.
    """
    alerts = alert_data.get('alerts', [])
    if not alerts:
        return None
    
    # Use the first alert for primary information
    primary_alert = alerts[0]
    
    # Extract basic information
    alert_name = primary_alert.get('labels', {}).get('alertname', 'Unknown Alert')
    severity = primary_alert.get('labels', {}).get('severity', 'unknown')
    instance = primary_alert.get('labels', {}).get('instance', 'unknown')
    
    # Create summary
    summary = f"[{severity.upper()}] {alert_name} - {instance}"
    
    # Create detailed description
    description_parts = [
        f"*Alert Details:*",
        f"• Alert Name: {alert_name}",
        f"• Severity: {severity}",
        f"• Instance: {instance}",
        f"• Status: {alert_data.get('status', 'unknown')}",
        f"• Received At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "*Affected Alerts:*"
    ]
    
    # Add details for each alert
    for i, alert in enumerate(alerts, 1):
        description_parts.extend([
            f"",
            f"*Alert {i}:*",
            f"• Summary: {alert.get('annotations', {}).get('summary', 'N/A')}",
            f"• Description: {alert.get('annotations', {}).get('description', 'N/A')}",
            f"• Started At: {alert.get('startsAt', 'N/A')}",
        ])
        
        # Add labels
        labels = alert.get('labels', {})
        if labels:
            description_parts.append("• Labels:")
            for key, value in labels.items():
                description_parts.append(f"  - {key}: {value}")
    
    # Add resolution information if alert is resolved
    if alert_data.get('status') == 'resolved':
        description_parts.extend([
            "",
            "*Resolution:*",
            f"• Resolved At: {primary_alert.get('endsAt', 'N/A')}",
            "• This alert has been automatically resolved."
        ])
    
    return {
        'summary': summary,
        'description': '\n'.join(description_parts),
        'priority': 'High' if severity == 'critical' else 'Medium',
        'labels': [f"alert-{alert_name.lower()}", f"severity-{severity}"],
        'alert_data': alert_data
    }

@app.route('/webhook/alert', methods=['POST'])
def handle_alert():
    """
    Handle incoming Prometheus alerts and create JIRA tickets.
    """
    try:
        # Log the incoming request
        logger.info(f"Received webhook request from {request.remote_addr}")
        
        # Parse the alert data
        alert_data = request.get_json()
        if not alert_data:
            logger.error("No JSON data received in webhook request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        logger.info(f"Processing alert: {json.dumps(alert_data, indent=2)}")
        
        # Format alert for JIRA
        jira_data = format_alert_for_jira(alert_data)
        if not jira_data:
            logger.warning("No valid alerts found in webhook data")
            return jsonify({'message': 'No valid alerts to process'}), 200
        
        # Send alert to Slack first
        slack_sent = send_alert_to_slack(alert_data)
        if slack_sent:
            logger.info("Alert sent to Slack successfully")
        else:
            logger.warning("Failed to send alert to Slack")
        
        # Create JIRA ticket
        result = jira_client.create_ticket(jira_data)
        
        # Store alert in database regardless of JIRA/Slack result
        alert_id = alert_store.store_alert(alert_data, result)
        
        if result['success']:
            logger.info(f"Successfully created JIRA ticket: {result['ticket_key']}, stored alert: {alert_id}")
            return jsonify({
                'message': 'Alert processed successfully',
                'ticket_key': result['ticket_key'],
                'ticket_url': result['ticket_url'],
                'alert_id': alert_id,
                'slack_sent': slack_sent
            }), 200
        else:
            logger.error(f"Failed to create JIRA ticket: {result['error']}, but stored alert: {alert_id}")
            return jsonify({
                'message': 'Alert processed and stored',
                'alert_id': alert_id,
                'jira_error': result['error'],
                'slack_sent': slack_sent
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    # Test Slack connectivity
    slack_status = False
    from slack_integration_enterprise import get_enterprise_slack_notifier
    slack_notifier = get_enterprise_slack_notifier()
    if slack_notifier:
        slack_status = slack_notifier.test_connection()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'jira_configured': jira_client.is_configured(),
        'database_connected': alert_store.is_connected(),
        'slack_connected': slack_status
    }), 200

@app.route('/test/slack', methods=['POST'])
def test_slack():
    """
    Test Slack integration with a sample alert.
    """
    try:
        # Create a test alert
        test_alert = {
            'alertname': 'Storage Test Alert',
            'status': 'firing',
            'labels': {
                'severity': 'warning',
                'instance': 'test-server',
                'device': '/dev/sda1',
                'mountpoint': '/',
                'fstype': 'ext4'
            },
            'annotations': {
                'summary': 'Test storage alert for Slack integration',
                'description': 'This is a test alert to verify Slack notifications are working correctly.'
            },
            'startsAt': datetime.now().isoformat(),
            'generatorURL': 'http://localhost:9090/test'
        }
        
        # Send to Slack
        slack_sent = send_alert_to_slack(test_alert)
        
        # Store in database
        alert_id = alert_store.store_alert(test_alert, {'success': False, 'error': 'Test alert - no JIRA ticket created'})
        
        return jsonify({
            'message': 'Test alert processed',
            'slack_sent': slack_sent,
            'alert_id': alert_id,
            'test_alert': test_alert
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing Slack integration: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to test Slack integration',
            'details': str(e)
        }), 500

@app.route('/api/alerts/live', methods=['GET'])
def get_live_alerts():
    """Get live alert stream for real-time monitoring."""
    try:
        # Get recent alerts from last 5 minutes
        alerts = alert_store.get_alerts(limit=20)
        
        # Filter for recent alerts (last 5 minutes)
        from datetime import datetime, timedelta
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        recent_alerts = []
        for alert in alerts:
            try:
                alert_time = datetime.fromisoformat(alert['timestamp'].replace(' ', 'T'))
                if alert_time >= five_minutes_ago:
                    recent_alerts.append(alert)
            except:
                # Include alerts with unparseable timestamps
                recent_alerts.append(alert)
        
        return jsonify({
            'alerts': recent_alerts[:10],  # Limit to 10 most recent
            'total_recent': len(recent_alerts),
            'monitoring_active': True,
            'last_updated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting live alerts: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to get live alerts',
            'details': str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    """
    Home page with webhook server information.
    """
    return jsonify({
        'service': 'Disk Monitoring Webhook Server',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'jira_configured': jira_client.is_configured(),
        'endpoints': {
            'webhook': '/webhook/alert',
            'health': '/health',
            'test': '/test'
        }
    })

@app.route('/test', methods=['GET', 'POST'])
def test_webhook():
    """
    Test endpoint for webhook functionality.
    """
    # Sample alert data for testing
    test_alert_data = {
        "version": "4",
        "groupKey": "{}:{alertname=\"DiskSpaceHigh\"}",
        "status": "firing",
        "receiver": "web.hook",
        "groupLabels": {
            "alertname": "DiskSpaceHigh"
        },
        "commonLabels": {
            "alertname": "DiskSpaceHigh",
            "instance": "localhost:9100",
            "job": "node",
            "severity": "warning"
        },
        "commonAnnotations": {
            "description": "Disk space usage is above 80% on localhost:9100",
            "summary": "High disk usage detected"
        },
        "externalURL": "http://localhost:9093",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "DiskSpaceHigh",
                    "device": "/dev/disk1s1",
                    "fstype": "apfs",
                    "instance": "localhost:9100",
                    "job": "node",
                    "mountpoint": "/",
                    "severity": "warning"
                },
                "annotations": {
                    "description": "Disk space usage is 85% on / (localhost:9100)",
                    "summary": "High disk usage detected on root filesystem"
                },
                "startsAt": "2024-01-01T12:00:00.000Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "http://localhost:9090/graph?g0.expr=..."
            }
        ]
    }
    
    if request.method == 'POST':
        # Process the test alert
        jira_data = format_alert_for_jira(test_alert_data)
        if jira_client.is_configured():
            result = jira_client.create_ticket(jira_data)
            return jsonify({
                'message': 'Test alert processed',
                'jira_result': result,
                'alert_data': test_alert_data
            })
        else:
            return jsonify({
                'message': 'Test alert formatted (JIRA not configured)',
                'formatted_data': jira_data,
                'alert_data': test_alert_data
            })
    else:
        # Return test alert data for GET requests
        return jsonify({
            'message': 'Test endpoint - POST to this URL to simulate an alert',
            'sample_alert': test_alert_data,
            'jira_configured': jira_client.is_configured(),
            'database_connected': alert_store.is_connected()
        })

# Database API endpoints
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get stored alerts from database."""
    try:
        limit = int(request.args.get('limit', 50))
        severity = request.args.get('severity')
        status = request.args.get('status')
        
        alerts = alert_store.get_alerts(limit=limit, severity=severity, status=status)
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'filters': {
                'limit': limit,
                'severity': severity,
                'status': status
            }
        })
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get specific alert by ID."""
    try:
        alert = alert_store.get_alert_by_id(alert_id)
        if alert:
            history = alert_store.get_alert_history(alert_id)
            return jsonify({
                'alert': alert,
                'history': history
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/status', methods=['PUT'])
def update_alert_status(alert_id):
    """Update alert status."""
    try:
        data = request.get_json()
        status = data.get('status')
        metadata = data.get('metadata', {})
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        success = alert_store.update_alert_status(alert_id, status, metadata)
        if success:
            return jsonify({'message': 'Alert status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update alert status'}), 500
    except Exception as e:
        logger.error(f"Error updating alert status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics."""
    try:
        stats = alert_store.get_alert_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_system_metrics():
    """Get stored system metrics."""
    try:
        hours = int(request.args.get('hours', 24))
        hostname = request.args.get('hostname')
        
        metrics = alert_store.get_system_metrics(hours=hours, hostname=hostname)
        
        return jsonify({
            'metrics': metrics,
            'count': len(metrics),
            'filters': {
                'hours': hours,
                'hostname': hostname
            }
        })
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/status', methods=['GET'])
def get_database_status():
    """Get database connection status and basic info."""
    try:
        if alert_store.is_connected():
            stats = alert_store.get_alert_stats()
            return jsonify({
                'connected': True,
                'database_type': 'SQLite',
                'database_file': 'alerts.db',
                'tables': {
                    'alerts': stats.get('total_alerts', 0),
                    'jira_tickets': stats.get('jira_tickets', 0),
                    'recent_24h': stats.get('recent_24h', 0)
                },
                'stats': stats
            })
        else:
            return jsonify({
                'connected': False,
                'error': 'Database not connected'
            }), 503
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check if JIRA is properly configured
    if not jira_client.is_configured():
        logger.warning("JIRA client is not properly configured. Check environment variables.")
    else:
        logger.info("JIRA client is configured and ready")
    
@app.route('/create-jira-ticket')
def create_jira_ticket():
    """Create JIRA ticket on-demand from Slack alert button."""
    try:
        # Extract parameters from URL
        alert_id = request.args.get('alert_id', 'unknown')
        alertname = request.args.get('alertname', 'Storage Alert')
        severity = request.args.get('severity', 'unknown')
        instance = request.args.get('instance', 'unknown')
        
        # Retrieve full alert details from database
        alert_details = None
        if alert_id != 'unknown':
            alert_details = alert_store.get_alert_by_id(alert_id)
        
        # Check if JIRA is configured
        if not jira_client.is_configured():
            return f"""
            <html>
            <head><title>JIRA Configuration Required</title></head>
            <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #d73502;">🔧 JIRA Configuration Required</h2>
                    <p>To create JIRA tickets automatically, please configure the following environment variables:</p>
                    <ul>
                        <li><strong>JIRA_URL</strong> - Your JIRA instance URL</li>
                        <li><strong>JIRA_USERNAME</strong> - JIRA username or email</li>
                        <li><strong>JIRA_API_TOKEN</strong> - JIRA API token</li>
                        <li><strong>JIRA_PROJECT_KEY</strong> - Project key (e.g., OPS, INFRA)</li>
                    </ul>
                    <h3>Alert Details:</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace;">
                        <strong>Alert:</strong> {alertname}<br>
                        <strong>Severity:</strong> {severity}<br>
                        <strong>Instance:</strong> {instance}<br>
                        <strong>Alert ID:</strong> {alert_id}
                    </div>
                    <p style="margin-top: 20px;">
                        <a href="http://localhost:3000" style="background: #0099ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Return to Dashboard</a>
                    </p>
                </div>
            </body>
            </html>
            """
        
        # Format alert data for JIRA ticket creation
        if alert_details:
            jira_data = format_alert_for_jira({'alerts': [alert_details]})
        else:
            # Create basic ticket from URL parameters
            jira_data = {
                'summary': f"{alertname} - {severity.upper()} on {instance}",
                'description': f"Alert escalated from Slack monitoring system.\n\nAlert: {alertname}\nSeverity: {severity}\nInstance: {instance}\nAlert ID: {alert_id}\n\nThis ticket was created automatically via on-call escalation.",
                'labels': ['storage-monitoring', 'automated', severity.lower()],
                'priority': 'High' if severity.lower() == 'critical' else 'Medium'
            }
        
        # Create JIRA ticket
        jira_result = jira_client.create_ticket(jira_data)
        
        if jira_result.get('success'):
            ticket_key = jira_result.get('ticket_key', 'Unknown')
            ticket_url = f"{jira_client.base_url}/browse/{ticket_key}"
            
            # Update alert with JIRA ticket information
            if alert_id != 'unknown':
                alert_store.update_alert_status(
                    alert_id, 
                    'escalated', 
                    {'jira_ticket': ticket_key, 'escalated_at': datetime.now().isoformat()}
                )
            
            return f"""
            <html>
            <head><title>JIRA Ticket Created</title></head>
            <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #28a745;">✅ JIRA Ticket Created Successfully</h2>
                    <div style="background: #d4edda; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        <strong>Ticket:</strong> <a href="{ticket_url}" target="_blank">{ticket_key}</a><br>
                        <strong>Alert:</strong> {alertname}<br>
                        <strong>Severity:</strong> {severity}<br>
                        <strong>Instance:</strong> {instance}
                    </div>
                    <p>The alert has been escalated and assigned to the operations team.</p>
                    <p>
                        <a href="{ticket_url}" target="_blank" style="background: #0099ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-right: 10px;">View JIRA Ticket</a>
                        <a href="http://localhost:3000" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Return to Dashboard</a>
                    </p>
                </div>
            </body>
            </html>
            """
        else:
            error_msg = jira_result.get('error', 'Unknown error occurred')
            return f"""
            <html>
            <head><title>JIRA Ticket Creation Failed</title></head>
            <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #d73502;">❌ JIRA Ticket Creation Failed</h2>
                    <div style="background: #f8d7da; padding: 15px; border-radius: 4px; margin: 20px 0;">
                        <strong>Error:</strong> {error_msg}<br>
                        <strong>Alert:</strong> {alertname}<br>
                        <strong>Severity:</strong> {severity}<br>
                        <strong>Instance:</strong> {instance}
                    </div>
                    <p>Please contact your system administrator or create the ticket manually.</p>
                    <p>
                        <a href="http://localhost:3000" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Return to Dashboard</a>
                    </p>
                </div>
            </body>
            </html>
            """
            
    except Exception as e:
        logger.error(f"Error creating JIRA ticket: {str(e)}")
        return f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
            <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #d73502;">❌ System Error</h2>
                <p>An unexpected error occurred: {str(e)}</p>
                <p>
                    <a href="http://localhost:3000" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Return to Dashboard</a>
                </p>
            </div>
        </body>
        </html>
        """, 500

@app.route('/runbooks/<alertname>')
def get_runbook(alertname):
    """Display runbook for specific alert type."""
    alert = request.args.get('alert', alertname)
    instance = request.args.get('instance', 'unknown')
    severity = request.args.get('severity', 'unknown')
    
    # Runbook templates based on alert type
    runbooks = {
        'diskspacecritical': {
            'title': 'Disk Space Critical Response',
            'steps': [
                '1. Immediately check disk usage: df -h',
                '2. Identify largest files/directories: du -sh /* | sort -hr',
                '3. Clear temporary files and logs if safe',
                '4. Consider log rotation or archival',
                '5. Expand storage if necessary',
                '6. Monitor until usage drops below 85%'
            ],
            'commands': [
                'df -h',
                'du -sh /* | sort -hr | head -10',
                'find /var/log -name "*.log" -size +100M',
                'journalctl --disk-usage'
            ]
        },
        'inodeusage': {
            'title': 'Inode Exhaustion Response',
            'steps': [
                '1. Check inode usage: df -i',
                '2. Find directories with many files: find / -xdev -type f | cut -d "/" -f 2 | sort | uniq -c | sort -n',
                '3. Clean up temporary files',
                '4. Remove unnecessary small files',
                '5. Consider filesystem restructuring'
            ],
            'commands': [
                'df -i',
                'find /tmp -type f | wc -l',
                'find /var/tmp -type f | wc -l'
            ]
        },
        'highsystemload': {
            'title': 'High System Load Response',
            'steps': [
                '1. Check current load: uptime',
                '2. Identify resource-heavy processes: top',
                '3. Check I/O wait: iostat 1 5',
                '4. Monitor disk activity: iotop',
                '5. Consider process optimization or scaling'
            ],
            'commands': [
                'uptime',
                'top -n 1',
                'iostat 1 5',
                'ps aux --sort=-%cpu | head -10'
            ]
        }
    }
    
    runbook = runbooks.get(alertname.lower(), {
        'title': f'{alert} Response Guide',
        'steps': [
            '1. Assess the current situation',
            '2. Check system logs for related errors',
            '3. Apply appropriate remediation steps',
            '4. Monitor system after changes',
            '5. Document actions taken'
        ],
        'commands': [
            'systemctl status',
            'journalctl -n 50',
            'dmesg | tail -20'
        ]
    })
    
    return f"""
    <html>
    <head><title>{runbook['title']}</title></head>
    <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #333;">📖 {runbook['title']}</h1>
            <div style="background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0;">
                <strong>Alert:</strong> {alert}<br>
                <strong>Instance:</strong> {instance}<br>
                <strong>Severity:</strong> {severity}
            </div>
            
            <h2>Response Steps:</h2>
            <ol>
                {''.join(f'<li style="margin: 10px 0;">{step}</li>' for step in runbook['steps'])}
            </ol>
            
            <h2>Diagnostic Commands:</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace;">
                {'<br>'.join(f'$ {cmd}' for cmd in runbook['commands'])}
            </div>
            
            <p style="margin-top: 30px;">
                <a href="http://localhost:3000" style="background: #0099ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-right: 10px;">Return to Dashboard</a>
                <a href="http://localhost:5000/create-jira-ticket?alertname={alert}&severity={severity}&instance={instance}" style="background: #d73502; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Create JIRA Ticket</a>
            </p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Start the Flask server
    logger.info("Starting webhook server on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)