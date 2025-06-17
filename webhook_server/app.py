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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize JIRA client
jira_client = JiraClient()

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
        
        if result['success']:
            logger.info(f"Successfully created JIRA ticket: {result['ticket_key']}")
            return jsonify({
                'message': 'JIRA ticket created successfully',
                'ticket_key': result['ticket_key'],
                'ticket_url': result['ticket_url']
            }), 200
        else:
            logger.error(f"Failed to create JIRA ticket: {result['error']}")
            return jsonify({
                'error': 'Failed to create JIRA ticket',
                'details': result['error']
            }), 500
            
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
        'jira_configured': jira_client.is_configured()
    }), 200

@app.route('/smart_metrics', methods=['GET'])
def smart_metrics():
    """
    Endpoint to serve SMART metrics in Prometheus format.
    """
    try:
        # Execute smartctl command to get disk health
        import subprocess
        
        metrics = []
        
        # Get list of disks
        result = subprocess.run(['diskutil', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to get disk list: {result.stderr}")
            return "# SMART metrics unavailable\n", 200
        
        # Parse disk identifiers
        disk_identifiers = []
        for line in result.stdout.split('\n'):
            if '/dev/disk' in line and 'physical' in line:
                parts = line.split()
                if parts:
                    disk_identifiers.append(parts[0])
        
        # Get SMART data for each disk
        for disk in disk_identifiers:
            try:
                # Run smartctl command
                smart_result = subprocess.run([
                    'smartctl', '-H', '-A', disk
                ], capture_output=True, text=True)
                
                if smart_result.returncode not in [0, 4]:  # 0 = OK, 4 = some SMART features disabled
                    continue
                
                # Parse SMART health
                health_ok = 1
                if 'SMART overall-health self-assessment test result: PASSED' not in smart_result.stdout:
                    health_ok = 0
                
                device_name = disk.replace('/dev/', '')
                metrics.append(f'smart_device_health_ok{{device="{device_name}"}} {health_ok}')
                
                # Parse attributes
                lines = smart_result.stdout.split('\n')
                in_attributes = False
                for line in lines:
                    if 'ID# ATTRIBUTE_NAME' in line:
                        in_attributes = True
                        continue
                    
                    if in_attributes and line.strip():
                        parts = line.split()
                        if len(parts) >= 10 and parts[0].isdigit():
                            attr_id = parts[0]
                            attr_name = parts[1]
                            value = parts[3]
                            worst = parts[4]
                            threshold = parts[5]
                            when_failed = parts[8] if len(parts) > 8 else ""
                            
                            try:
                                metrics.append(f'smart_attribute_value{{device="{device_name}",attribute_id="{attr_id}",attribute_name="{attr_name}",when_failed="{when_failed}"}} {value}')
                                metrics.append(f'smart_attribute_worst{{device="{device_name}",attribute_id="{attr_id}",attribute_name="{attr_name}"}} {worst}')
                                metrics.append(f'smart_attribute_threshold{{device="{device_name}",attribute_id="{attr_id}",attribute_name="{attr_name}"}} {threshold}')
                            except ValueError:
                                continue
                            
            except Exception as e:
                logger.warning(f"Failed to get SMART data for {disk}: {e}")
                continue
        
        return '\n'.join(metrics) + '\n', 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Error generating SMART metrics: {e}")
        return "# SMART metrics error\n", 500, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    # Check if JIRA is properly configured
    if not jira_client.is_configured():
        logger.warning("JIRA client is not properly configured. Check environment variables.")
    
    # Start the Flask server
    logger.info("Starting webhook server on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
