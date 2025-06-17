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
from database.alert_store import AlertStore

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
alert_store = AlertStore()

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
        
        # Create JIRA ticket
        result = jira_client.create_ticket(jira_data)
        
        # Store alert in database regardless of JIRA result
        alert_id = alert_store.store_alert(alert_data, result)
        
        if result['success']:
            logger.info(f"Successfully created JIRA ticket: {result['ticket_key']}, stored alert: {alert_id}")
            return jsonify({
                'message': 'JIRA ticket created successfully',
                'ticket_key': result['ticket_key'],
                'ticket_url': result['ticket_url'],
                'alert_id': alert_id
            }), 200
        else:
            logger.error(f"Failed to create JIRA ticket: {result['error']}, but stored alert: {alert_id}")
            return jsonify({
                'message': 'Alert processed and stored',
                'alert_id': alert_id,
                'jira_error': result['error']
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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'jira_configured': jira_client.is_configured(),
        'database_connected': alert_store.is_connected()
    }), 200

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
                'database': alert_store.database_name,
                'collections': {
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
    
    # Start the Flask server
    logger.info("Starting webhook server on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)