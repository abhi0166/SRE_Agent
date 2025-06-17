#!/usr/bin/env python3
"""
JIRA client for creating tickets from Prometheus alerts.
"""

import os
import json
import logging
import requests
from base64 import b64encode
from datetime import datetime

logger = logging.getLogger(__name__)

class JiraClient:
    """
    Client for interacting with JIRA API to create tickets.
    """
    
    def __init__(self):
        """
        Initialize JIRA client with configuration from environment variables.
        """
        self.jira_url = os.getenv('JIRA_URL', '')
        self.jira_username = os.getenv('JIRA_USERNAME', '')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN', '')
        self.jira_project = os.getenv('JIRA_PROJECT', 'DCOPS')
        self.jira_assignee = os.getenv('JIRA_ASSIGNEE', 'datacenter.ops')
        self.jira_issue_type = os.getenv('JIRA_ISSUE_TYPE', 'Task')
        
        # Create authorization header
        if self.jira_username and self.jira_api_token:
            credentials = f"{self.jira_username}:{self.jira_api_token}"
            encoded_credentials = b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded_credentials}"
        else:
            self.auth_header = None
            
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.auth_header:
            self.headers['Authorization'] = self.auth_header
    
    def is_configured(self):
        """
        Check if JIRA client is properly configured.
        """
        required_vars = [self.jira_url, self.jira_username, self.jira_api_token, self.jira_project]
        return all(var for var in required_vars)
    
    def test_connection(self):
        """
        Test connection to JIRA instance.
        """
        if not self.is_configured():
            return {'success': False, 'error': 'JIRA client not configured'}
        
        try:
            # Try API v3 first (recommended for Cloud)
            url = f"{self.jira_url}/rest/api/3/myself"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    'success': True,
                    'user': user_info.get('displayName', 'Unknown'),
                    'email': user_info.get('emailAddress', 'Unknown'),
                    'account_id': user_info.get('accountId', 'Unknown')
                }
            elif response.status_code == 401:
                # Provide specific guidance for authentication issues
                error_msg = "Authentication failed. For Atlassian Cloud, ensure:\n"
                error_msg += "- Username is your full email address\n"
                error_msg += "- API token is valid and from Account Settings > Security > API tokens\n"
                error_msg += "- Account has access to the JIRA instance"
                return {'success': False, 'error': error_msg}
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_project_info(self):
        """
        Get project information to validate configuration.
        """
        if not self.is_configured():
            return {'success': False, 'error': 'JIRA client not configured'}
        
        try:
            url = f"{self.jira_url}/rest/api/2/project/{self.jira_project}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                project_info = response.json()
                return {
                    'success': True,
                    'project': project_info
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_ticket(self, ticket_data):
        """
        Create a JIRA ticket from alert data.
        
        Args:
            ticket_data (dict): Formatted ticket data containing summary, description, etc.
            
        Returns:
            dict: Result of ticket creation with success status and ticket key
        """
        if not self.is_configured():
            logger.error("JIRA client not configured")
            return {'success': False, 'error': 'JIRA client not configured'}
        
        try:
            # Prepare ticket payload
            payload = {
                'fields': {
                    'project': {
                        'key': self.jira_project
                    },
                    'summary': ticket_data['summary'][:250],  # JIRA summary limit
                    'description': ticket_data['description'],
                    'issuetype': {
                        'name': self.jira_issue_type
                    },
                    'priority': {
                        'name': ticket_data.get('priority', 'Medium')
                    }
                }
            }
            
            # Add assignee if specified
            if self.jira_assignee:
                payload['fields']['assignee'] = {
                    'name': self.jira_assignee
                }
            
            # Add labels if provided
            if 'labels' in ticket_data and ticket_data['labels']:
                # Sanitize labels to remove spaces and special characters
                sanitized_labels = []
                for label in ticket_data['labels']:
                    import re
                    clean_label = re.sub(r'[^a-zA-Z0-9_-]', '-', str(label).lower()).strip('-')
                    if clean_label:
                        sanitized_labels.append(clean_label)
                
                payload['fields']['labels'] = sanitized_labels
                logger.info(f"JIRA labels: {sanitized_labels}")
            
            # Log the payload for debugging
            logger.info(f"Creating JIRA ticket: {payload['fields']['summary']}")
            
            # Make API request
            url = f"{self.jira_url}/rest/api/2/issue"
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 201:
                ticket_info = response.json()
                ticket_key = ticket_info['key']
                ticket_url = f"{self.jira_url}/browse/{ticket_key}"
                
                logger.info(f"Successfully created JIRA ticket {ticket_key}")
                
                return {
                    'success': True,
                    'ticket_key': ticket_key,
                    'ticket_url': ticket_url,
                    'ticket_id': ticket_info['id']
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to create JIRA ticket: {error_msg}")
                
                # Try to parse error details
                try:
                    error_details = response.json()
                    if 'errors' in error_details:
                        error_msg += f" - Errors: {error_details['errors']}"
                    if 'errorMessages' in error_details:
                        error_msg += f" - Messages: {error_details['errorMessages']}"
                except:
                    pass
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout when creating JIRA ticket"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error when creating JIRA ticket"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error creating JIRA ticket: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': error_msg}
    
    def update_ticket(self, ticket_key, update_data):
        """
        Update an existing JIRA ticket.
        
        Args:
            ticket_key (str): JIRA ticket key
            update_data (dict): Data to update
            
        Returns:
            dict: Result of update operation
        """
        if not self.is_configured():
            return {'success': False, 'error': 'JIRA client not configured'}
        
        try:
            url = f"{self.jira_url}/rest/api/2/issue/{ticket_key}"
            
            payload = {
                'fields': update_data
            }
            
            response = requests.put(
                url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 204:
                logger.info(f"Successfully updated JIRA ticket {ticket_key}")
                return {'success': True}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to update JIRA ticket {ticket_key}: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f"Error updating JIRA ticket {ticket_key}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': error_msg}