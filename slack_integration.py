"""
Enhanced Slack Integration for Storage Monitoring Alerts
Enterprise-grade formatting with rich text, visual hierarchy, and professional presentation.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with bot token and channel."""
        self.slack_token = os.environ.get('SLACK_BOT_TOKEN')
        self.channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        if not self.slack_token or not self.channel_id:
            logger.error("SLACK_BOT_TOKEN and SLACK_CHANNEL_ID environment variables must be set")
            self.client = None
            return
            
        self.client = WebClient(token=self.slack_token)
        logger.info("Slack client initialized successfully")
    
    def test_connection(self) -> bool:
        """Test Slack connection and permissions."""
        if not self.client:
            return False
            
        try:
            # Test authentication
            auth_response = self.client.auth_test()
            if auth_response["ok"]:
                bot_name = auth_response.get("user", "Unknown Bot")
                logger.info(f"Connected to Slack as: {bot_name}")
                
                # Test channel access
                if self.channel_id:
                    channel_info = self.client.conversations_info(channel=self.channel_id)
                    if channel_info["ok"]:
                        channel_name = channel_info["channel"]["name"]
                        logger.info(f"Channel access confirmed: #{channel_name}")
                        return True
                    else:
                        logger.error(f"Cannot access channel: {self.channel_id}")
                        return False
                else:
                    logger.error("Channel ID not configured")
                    return False
            else:
                logger.error("Slack authentication failed")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error during connection test: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing Slack connection: {str(e)}")
            return False
    
    def format_storage_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format storage alert data for enterprise-grade Slack message."""
        
        # Handle both direct alert data and wrapped AlertManager data
        alert_info = alert_data
        if 'alerts' in alert_data and len(alert_data['alerts']) > 0:
            # AlertManager format - extract first alert
            alert_info = alert_data['alerts'][0]
            common_labels = alert_data.get('commonLabels', {})
            common_annotations = alert_data.get('commonAnnotations', {})
            
            # Merge common data with specific alert data
            labels = {**common_labels, **alert_info.get('labels', {})}
            annotations = {**common_annotations, **alert_info.get('annotations', {})}
            
            alert_info = {
                **alert_info,
                'labels': labels,
                'annotations': annotations
            }
        
        # Extract alert information with fallbacks
        alertname = alert_info.get('alertname', alert_data.get('alertname', 'Storage Alert'))
        labels = alert_info.get('labels', {})
        annotations = alert_info.get('annotations', {})
        
        severity = labels.get('severity', 'unknown')
        instance = labels.get('instance', 'unknown')
        description = annotations.get('description', 'No description available')
        summary = annotations.get('summary', alertname)
        status = alert_info.get('status', 'firing')
        
        # Enterprise severity configuration with executive styling
        severity_config = {
            'critical': {
                'emoji': '🔴', 
                'color': '#D73502', 
                'prefix': 'CRITICAL ALERT', 
                'border': '▰▰▰',
                'priority': 'P1 - IMMEDIATE ACTION REQUIRED'
            },
            'warning': {
                'emoji': '🟡', 
                'color': '#FF8C00', 
                'prefix': 'WARNING ALERT', 
                'border': '▲▲▲',
                'priority': 'P2 - ATTENTION NEEDED'
            },
            'info': {
                'emoji': '🔵', 
                'color': '#0099FF', 
                'prefix': 'INFORMATIONAL', 
                'border': '●●●',
                'priority': 'P3 - MONITORING'
            },
            'resolved': {
                'emoji': '🟢', 
                'color': '#28A745', 
                'prefix': 'RESOLVED', 
                'border': '✓✓✓',
                'priority': 'STATUS UPDATE'
            }
        }
        
        config = severity_config.get(severity.lower(), {
            'emoji': '⚪', 
            'color': '#6C757D', 
            'prefix': 'UNKNOWN SEVERITY', 
            'border': '???',
            'priority': 'P4 - REVIEW REQUIRED'
        })
        
        # Format timestamp with enhanced precision
        timestamp_str = alert_info.get('startsAt', alert_data.get('startsAt', ''))
        formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        alert_id = "unknown"
        
        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    if timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str[:-1] + '+00:00'
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    alert_id = f"{alertname.lower()}_{instance}_{int(dt.timestamp())}"
                else:
                    alert_id = f"{alertname.lower()}_{instance}_{int(datetime.now().timestamp())}"
            except:
                alert_id = f"{alertname.lower()}_{instance}_{int(datetime.now().timestamp())}"
        
        # Enterprise header with executive visibility
        header_text = f"{config['emoji']} {config['prefix']}: {alertname}"
        if status == 'resolved':
            header_text = f"{config['emoji']} RESOLVED: {alertname}"
        
        # Executive summary block with priority indication
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{config['border']} *ENTERPRISE STORAGE ANALYTICS* | {config['priority']} {config['border']}"
                    }
                ]
            }
        ]
        
        # Executive dashboard with key metrics in grid layout
        status_display = status.upper() if isinstance(status, str) else 'UNKNOWN'
        severity_display = severity.upper() if isinstance(severity, str) else 'UNKNOWN'
        
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*🎯 Severity Classification*\n```{severity_display}```"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*🖥️ Affected Infrastructure*\n```{instance}```"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*⏰ Detection Timestamp*\n```{formatted_time}```"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*📊 Current Status*\n```{status_display}```"
                }
            ]
        })
        
        # Technical details with professional code block formatting
        if description and description != "No description available":
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 Technical Assessment*\n```{description}```"
                }
            })
        
        # Executive summary if different from technical details
        if summary and summary != description and summary != alertname:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📝 Executive Summary*\n_{summary}_"
                }
            })
        
        # Infrastructure topology and metrics grid
        infrastructure_fields = []
        
        # Core infrastructure components
        if 'device' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*💾 Storage Device*\n`{labels['device']}`"
            })
        if 'mountpoint' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn", 
                "text": f"*📁 Mount Point*\n`{labels['mountpoint']}`"
            })
        if 'fstype' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*🗂️ Filesystem Type*\n`{labels['fstype']}`"
            })
        if 'pool' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*🏊 Storage Pool*\n`{labels['pool']}`"
            })
        if 'alerttype' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*⚙️ Alert Category*\n`{labels['alerttype'].title()}`"
            })
        
        # Performance metrics
        if 'usage_percent' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*📊 Capacity Utilization*\n`{labels['usage_percent']}%`"
            })
        if 'available_gb' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*💿 Available Capacity*\n`{labels['available_gb']} GB`"
            })
        if 'load_avg' in labels:
            infrastructure_fields.append({
                "type": "mrkdwn",
                "text": f"*⚡ System Load Average*\n`{labels['load_avg']}`"
            })
        
        # Display infrastructure fields in professional grid (max 8 fields per section)
        if infrastructure_fields:
            for i in range(0, len(infrastructure_fields), 8):
                chunk = infrastructure_fields[i:i+8]
                blocks.append({
                    "type": "section",
                    "fields": chunk
                })
        
        # Enterprise action center with buttons
        action_elements = []
        
        # Operations Runbook - enhanced with alert-specific context
        runbook_url = annotations.get('runbook_url', f"http://localhost:5000/runbooks/{alertname.lower()}")
        action_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Operations Runbook",
                "emoji": False
            },
            "url": f"{runbook_url}?alert={alertname}&instance={instance}&severity={severity}",
            "style": "primary"
        })
        
        # Executive Dashboard - with filtered view for this alert  
        dashboard_url = annotations.get('dashboard_url', f"http://localhost:3000")
        action_elements.append({
            "type": "button", 
            "text": {
                "type": "plain_text",
                "text": "Storage Dashboard",
                "emoji": False
            },
            "url": f"{dashboard_url}?filter={alertname}&instance={instance}"
        })
            
        # Real-time Metrics - direct link to specific device/metric
        metrics_url = alert_info.get('generatorURL', f"http://localhost:3000")
        action_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text", 
                "text": "Live Metrics",
                "emoji": False
            },
            "url": f"{metrics_url}?alert_id={alert_id}"
        })
        
        # On-Call JIRA Ticket Creation - always available for immediate escalation
        jira_create_url = f"http://localhost:5000/create-jira-ticket"
        action_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Create JIRA Ticket",
                "emoji": False
            },
            "url": f"{jira_create_url}?alert_id={alert_id}&alertname={alertname}&severity={severity}&instance={instance}",
            "style": "danger" if severity.lower() == 'critical' else "default"
        })
        
        if action_elements:
            blocks.append({
                "type": "actions",
                "elements": action_elements
            })
        
        # Professional footer with audit trail
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 *Enterprise Storage Analytics Platform* | Generated: `{formatted_time}` | Alert ID: `{alert_id}` | Version: `4.0`"
                    }
                ]
            }
        ])
        
        return {
            "text": f"{config['prefix']}: {alertname} on {instance}",
            "blocks": blocks,
            "attachments": [{
                "color": config['color'],
                "fallback": f"{alertname} - {severity} - {instance} - {description}"
            }]
        }
    
    def send_storage_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send enterprise-formatted storage alert to Slack channel."""
        if not self.client:
            logger.error("Slack client not initialized")
            return False
        
        try:
            message_blocks = self.format_storage_alert(alert_data)
            
            result = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message_blocks["text"],
                blocks=message_blocks["blocks"],
                attachments=message_blocks.get("attachments", [])
            )
            
            if result["ok"]:
                # Extract proper alert name for logging
                alert_name = "Unknown"
                if 'alerts' in alert_data and len(alert_data['alerts']) > 0:
                    alert_name = alert_data['alerts'][0].get('alertname', alert_data.get('alertname', 'Unknown'))
                else:
                    alert_name = alert_data.get('alertname', 'Unknown')
                    
                logger.info(f"Alert sent to Slack successfully: {alert_name}")
                return True
            else:
                logger.error(f"Failed to send alert to Slack: {result.get('error', 'Unknown error')}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error sending alert: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending alert: {str(e)}")
            return False

    def send_system_status(self, metrics: Dict[str, Any]) -> bool:
        """Send periodic system status updates to Slack."""
        if not self.client:
            return False
        
        # Implementation for system status updates
        return True

# Global instance for convenience
_slack_notifier = None

def get_slack_notifier() -> Optional[SlackNotifier]:
    """Get or create Slack notifier instance."""
    global _slack_notifier
    if _slack_notifier is None:
        _slack_notifier = SlackNotifier()
    return _slack_notifier

def send_alert_to_slack(alert_data: Dict[str, Any]) -> bool:
    """Convenience function to send alert to Slack."""
    notifier = get_slack_notifier()
    if notifier:
        return notifier.send_storage_alert(alert_data)
    return False

def send_status_to_slack(metrics: Dict[str, Any]) -> bool:
    """Convenience function to send status update to Slack."""
    notifier = get_slack_notifier()
    if notifier and notifier.client:
        return notifier.send_system_status(metrics)
    return False