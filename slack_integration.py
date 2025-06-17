"""
Slack Integration for Storage Monitoring Alerts
Sends formatted storage alerts to Slack channels with rich formatting.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackNotifier:
    def __init__(self):
        """Initialize Slack client with bot token and channel."""
        self.slack_token = os.environ.get('SLACK_BOT_TOKEN')
        self.slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
        
        if not self.slack_token:
            logger.error("SLACK_BOT_TOKEN environment variable not set")
            raise ValueError("SLACK_BOT_TOKEN is required")
            
        if not self.slack_channel_id:
            logger.error("SLACK_CHANNEL_ID environment variable not set")
            raise ValueError("SLACK_CHANNEL_ID is required")
        
        self.client = WebClient(token=self.slack_token)
        logger.info("Slack client initialized successfully")
    
    def test_connection(self) -> bool:
        """Test Slack connection and permissions."""
        try:
            # Test auth
            auth_response = self.client.auth_test()
            logger.info(f"Connected to Slack as: {auth_response['user']}")
            
            # Test channel access
            channel_info = self.client.conversations_info(channel=self.slack_channel_id)
            logger.info(f"Channel access confirmed: #{channel_info['channel']['name']}")
            
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack connection test failed: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing Slack connection: {str(e)}")
            return False
    
    def format_storage_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format storage alert data for Slack message."""
        
        # Extract alert information
        alertname = alert_data.get('alertname', 'Storage Alert')
        severity = alert_data.get('labels', {}).get('severity', 'unknown')
        instance = alert_data.get('labels', {}).get('instance', 'unknown')
        description = alert_data.get('annotations', {}).get('description', 'No description available')
        summary = alert_data.get('annotations', {}).get('summary', '')
        
        # Determine emoji and color based on severity
        severity_config = {
            'critical': {'emoji': '🚨', 'color': '#FF0000'},
            'warning': {'emoji': '⚠️', 'color': '#FFA500'},
            'info': {'emoji': 'ℹ️', 'color': '#0066CC'},
            'unknown': {'emoji': '❓', 'color': '#808080'}
        }
        
        config = severity_config.get(severity.lower(), severity_config['unknown'])
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Create Slack blocks for rich formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{config['emoji']} Storage Alert: {alertname}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Instance:* {instance}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {timestamp}"
                    }
                ]
            }
        ]
        
        # Add description if available
        if description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{description}"
                }
            })
        
        # Add summary if available and different from description
        if summary and summary != description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary}"
                }
            })
        
        # Add device/filesystem specific information if available
        labels = alert_data.get('labels', {})
        if 'device' in labels or 'fstype' in labels or 'mountpoint' in labels:
            device_info = []
            if 'device' in labels:
                device_info.append(f"*Device:* {labels['device']}")
            if 'mountpoint' in labels:
                device_info.append(f"*Mount:* {labels['mountpoint']}")
            if 'fstype' in labels:
                device_info.append(f"*Filesystem:* {labels['fstype']}")
            
            if device_info:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(device_info)
                    }
                })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        return {
            "channel": self.slack_channel_id,
            "blocks": blocks,
            "attachments": [
                {
                    "color": config['color'],
                    "footer": "Storage Monitoring System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
    
    def send_storage_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send storage alert to Slack channel."""
        try:
            # Format the alert message
            message_data = self.format_storage_alert(alert_data)
            
            # Send message to Slack
            response = self.client.chat_postMessage(**message_data)
            
            if response['ok']:
                logger.info(f"Alert sent to Slack successfully: {alert_data.get('alertname', 'Unknown')}")
                return True
            else:
                logger.error(f"Failed to send alert to Slack: {response.get('error', 'Unknown error')}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error sending alert: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending alert to Slack: {str(e)}")
            return False
    
    def send_system_status(self, metrics: Dict[str, Any]) -> bool:
        """Send periodic system status updates to Slack."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Create status message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Storage System Status Update"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Timestamp:* {timestamp}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {'🟢 Healthy' if metrics.get('overall_health', 'unknown') == 'healthy' else '🟡 Warning'}"
                        }
                    ]
                }
            ]
            
            # Add key metrics
            if 'disk_usage' in metrics:
                disk_info = []
                for disk, usage in metrics['disk_usage'].items():
                    status_emoji = "🔴" if usage > 90 else "🟡" if usage > 80 else "🟢"
                    disk_info.append(f"{status_emoji} {disk}: {usage:.1f}%")
                
                if disk_info:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Disk Usage:*\n" + "\n".join(disk_info)
                        }
                    })
            
            message_data = {
                "channel": self.slack_channel_id,
                "blocks": blocks,
                "attachments": [
                    {
                        "color": "#36a64f",
                        "footer": "Storage Monitoring System - Periodic Update",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = self.client.chat_postMessage(**message_data)
            
            if response['ok']:
                logger.info("System status sent to Slack successfully")
                return True
            else:
                logger.error(f"Failed to send status to Slack: {response.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending system status to Slack: {str(e)}")
            return False

# Global instance
slack_notifier = None

def get_slack_notifier() -> Optional[SlackNotifier]:
    """Get or create Slack notifier instance."""
    global slack_notifier
    
    if slack_notifier is None:
        try:
            slack_notifier = SlackNotifier()
            # Test connection on first initialization
            if not slack_notifier.test_connection():
                logger.error("Slack connection test failed during initialization")
                slack_notifier = None
        except Exception as e:
            logger.error(f"Failed to initialize Slack notifier: {str(e)}")
            slack_notifier = None
    
    return slack_notifier

def send_alert_to_slack(alert_data: Dict[str, Any]) -> bool:
    """Convenience function to send alert to Slack."""
    notifier = get_slack_notifier()
    if notifier:
        return notifier.send_storage_alert(alert_data)
    return False

def send_status_to_slack(metrics: Dict[str, Any]) -> bool:
    """Convenience function to send status update to Slack."""
    notifier = get_slack_notifier()
    if notifier:
        return notifier.send_system_status(metrics)
    return False