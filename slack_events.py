"""
Slack Events API Integration for Interactive Alert Assignment
Handles emoji reactions to automatically assign users to storage alerts.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from database.sqlite_store import SQLiteAlertStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackEventsHandler:
    """
    Handles Slack Events API for interactive alert assignment through emoji reactions.
    """
    
    def __init__(self):
        """Initialize Slack Events handler with bot token and database."""
        self.slack_token = os.environ.get('SLACK_BOT_TOKEN')
        self.slack_channel = os.environ.get('SLACK_CHANNEL_ID')
        
        if not self.slack_token:
            logger.error("SLACK_BOT_TOKEN environment variable not set")
            return
            
        self.client = WebClient(token=self.slack_token)
        self.db_store = SQLiteAlertStore()
        
    def verify_url_challenge(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Handle Slack URL verification challenge for Events API setup.
        
        Args:
            event_data: Event data from Slack
            
        Returns:
            Challenge string if this is a verification request
        """
        if event_data.get('type') == 'url_verification':
            return event_data.get('challenge')
        return None
    
    def handle_reaction_added(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle emoji reaction added to a message.
        
        Args:
            event_data: Slack event data
            
        Returns:
            Success status
        """
        try:
            event = event_data.get('event', {})
            
            # Extract reaction details
            reaction = event.get('reaction')
            user_id = event.get('user')
            message_ts = event.get('item', {}).get('ts')
            channel = event.get('item', {}).get('channel')
            
            # Check if this is a "taking a look" reaction (eyes emoji or similar)
            taking_look_emojis = ['eyes', 'mag', 'hammer_and_wrench', 'tools', 'gear']
            
            if reaction not in taking_look_emojis:
                logger.info(f"Ignoring reaction '{reaction}' - not a assignment emoji")
                return True
                
            # Get user information
            user_info = self._get_user_info(user_id)
            if not user_info:
                logger.error(f"Could not get user info for {user_id}")
                return False
                
            username = user_info.get('real_name') or user_info.get('display_name') or user_info.get('name', 'Unknown User')
            
            # Find the alert associated with this message
            alert_id = self._find_alert_by_message_ts(message_ts)
            if not alert_id:
                logger.warning(f"Could not find alert for message timestamp {message_ts}")
                return False
                
            # Assign user to the alert
            success = self._assign_user_to_alert(alert_id, user_id, username)
            
            if success:
                # Update the original Slack message to show assignment
                self._update_message_with_assignment(channel, message_ts, username, reaction)
                logger.info(f"Successfully assigned {username} to alert {alert_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error handling reaction added: {str(e)}")
            return False
    
    def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Slack API."""
        try:
            response = self.client.users_info(user=user_id)
            return response.get('user', {})
        except SlackApiError as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def _find_alert_by_message_ts(self, message_ts: str) -> Optional[str]:
        """
        Find alert ID by matching message timestamp in database.
        
        This requires storing message timestamps when alerts are sent.
        """
        try:
            # Search for alerts with matching Slack message timestamp
            alerts = self.db_store.get_alerts(limit=100)
            
            for alert in alerts:
                alert_metadata = alert.get('metadata', {})
                if alert_metadata.get('slack_message_ts') == message_ts:
                    return alert.get('alert_id')
                    
            return None
            
        except Exception as e:
            logger.error(f"Error finding alert by message timestamp: {str(e)}")
            return None
    
    def _assign_user_to_alert(self, alert_id: str, user_id: str, username: str) -> bool:
        """
        Assign user to alert in database and update status.
        
        Args:
            alert_id: Alert identifier
            user_id: Slack user ID
            username: User display name
            
        Returns:
            Success status
        """
        try:
            # Update alert status to assigned
            assignment_metadata = {
                'assigned_to_slack_user': user_id,
                'assigned_to_username': username,
                'assigned_at': datetime.now().isoformat(),
                'assignment_method': 'slack_reaction'
            }
            
            success = self.db_store.update_alert_status(
                alert_id=alert_id,
                status='assigned',
                metadata=assignment_metadata
            )
            
            if success:
                logger.info(f"Updated alert {alert_id} assignment to {username}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error assigning user to alert: {str(e)}")
            return False
    
    def _update_message_with_assignment(self, channel: str, message_ts: str, username: str, reaction: str) -> bool:
        """
        Update the original Slack message to show user assignment.
        
        Args:
            channel: Slack channel ID
            message_ts: Message timestamp
            username: Assigned user name
            reaction: Emoji reaction used
            
        Returns:
            Success status
        """
        try:
            # Get the original message
            response = self.client.conversations_history(
                channel=channel,
                latest=message_ts,
                limit=1,
                inclusive=True
            )
            
            messages = response.get('messages', [])
            if not messages:
                logger.error("Could not find original message to update")
                return False
                
            original_message = messages[0]
            blocks = original_message.get('blocks', [])
            
            # Add assignment section to the message blocks
            assignment_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"👨‍💻 *Assigned to:* {username} (:{reaction}:)"
                }
            }
            
            # Add assignment block if not already present
            assignment_exists = any(
                block.get('text', {}).get('text', '').startswith('👨‍💻 *Assigned to:*')
                for block in blocks
                if block.get('type') == 'section'
            )
            
            if not assignment_exists:
                blocks.append(assignment_block)
                
                # Update the message
                self.client.chat_update(
                    channel=channel,
                    ts=message_ts,
                    blocks=blocks
                )
                
                logger.info(f"Updated message with assignment to {username}")
                
            return True
            
        except SlackApiError as e:
            logger.error(f"Error updating message with assignment: {e}")
            return False
    
    def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main event handler for Slack Events API.
        
        Args:
            event_data: Raw event data from Slack
            
        Returns:
            Response data for Slack
        """
        try:
            # Handle URL verification challenge
            challenge = self.verify_url_challenge(event_data)
            if challenge:
                return {'challenge': challenge}
            
            # Handle different event types
            event = event_data.get('event', {})
            event_type = event.get('type')
            
            if event_type == 'reaction_added':
                success = self.handle_reaction_added(event_data)
                return {'status': 'success' if success else 'error'}
            
            elif event_type == 'reaction_removed':
                # Could handle unassignment here if needed
                logger.info("Reaction removed event - ignoring for now")
                return {'status': 'ignored'}
            
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {'status': 'ignored'}
                
        except Exception as e:
            logger.error(f"Error handling Slack event: {str(e)}")
            return {'status': 'error', 'message': str(e)}

# Global instance
slack_events_handler = SlackEventsHandler()

def handle_slack_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to handle Slack events.
    
    Args:
        event_data: Raw event data from Slack
        
    Returns:
        Response data for Slack
    """
    return slack_events_handler.handle_event(event_data)