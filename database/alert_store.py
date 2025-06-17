#!/usr/bin/env python3
"""
MongoDB database layer for storing alerts and metadata.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError

logger = logging.getLogger(__name__)

class AlertStore:
    """
    MongoDB-based storage for alerts and metadata.
    """
    
    def __init__(self, connection_string=None, database_name="monitoring"):
        """
        Initialize the alert store.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name to use
        """
        self.connection_string = connection_string or os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
        self.database_name = database_name
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self._setup_collections()
            logger.info(f"Connected to MongoDB: {self.database_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
    
    def _setup_collections(self):
        """Setup collections and indexes."""
        if not self.db:
            return
        
        # Alerts collection
        alerts = self.db.alerts
        alerts.create_index([("alert_id", 1)], unique=True)
        alerts.create_index([("timestamp", -1)])
        alerts.create_index([("severity", 1)])
        alerts.create_index([("status", 1)])
        alerts.create_index([("alertname", 1)])
        alerts.create_index([("instance", 1)])
        
        # Alert history collection
        history = self.db.alert_history
        history.create_index([("alert_id", 1)])
        history.create_index([("timestamp", -1)])
        history.create_index([("action", 1)])
        
        # System metrics collection
        metrics = self.db.system_metrics
        metrics.create_index([("timestamp", -1)])
        metrics.create_index([("hostname", 1)])
        metrics.create_index([("metric_type", 1)])
        
        # JIRA tickets collection
        tickets = self.db.jira_tickets
        tickets.create_index([("alert_id", 1)])
        tickets.create_index([("ticket_key", 1)], unique=True, sparse=True)
        tickets.create_index([("created_at", -1)])
    
    def is_connected(self):
        """Check if database is connected."""
        return self.client is not None and self.db is not None
    
    def store_alert(self, alert_data: Dict, jira_result: Optional[Dict] = None) -> str:
        """
        Store an alert in the database.
        
        Args:
            alert_data: Formatted alert data
            jira_result: JIRA ticket creation result
            
        Returns:
            Alert ID
        """
        if not self.is_connected():
            logger.error("Database not connected")
            return None
        
        try:
            # Extract key information
            alerts = alert_data.get('alerts', [])
            if not alerts:
                return None
            
            primary_alert = alerts[0]
            labels = primary_alert.get('labels', {})
            
            # Generate alert ID
            alert_id = f"{labels.get('alertname', 'unknown')}_{labels.get('instance', 'unknown')}_{int(datetime.now().timestamp())}"
            
            # Prepare document
            alert_doc = {
                'alert_id': alert_id,
                'timestamp': datetime.now(timezone.utc),
                'alertname': labels.get('alertname', 'unknown'),
                'instance': labels.get('instance', 'unknown'),
                'severity': labels.get('severity', 'unknown'),
                'status': alert_data.get('status', 'firing'),
                'labels': labels,
                'annotations': primary_alert.get('annotations', {}),
                'starts_at': primary_alert.get('startsAt'),
                'ends_at': primary_alert.get('endsAt'),
                'raw_alert_data': alert_data,
                'processed': True
            }
            
            # Add JIRA information if available
            if jira_result:
                alert_doc['jira'] = {
                    'ticket_created': jira_result.get('success', False),
                    'ticket_key': jira_result.get('ticket_key'),
                    'ticket_url': jira_result.get('ticket_url'),
                    'error': jira_result.get('error'),
                    'created_at': datetime.now(timezone.utc)
                }
            
            # Insert alert
            self.db.alerts.insert_one(alert_doc)
            
            # Store in history
            self._add_alert_history(alert_id, 'created', alert_doc)
            
            # Store JIRA ticket separately if created
            if jira_result and jira_result.get('success'):
                self._store_jira_ticket(alert_id, jira_result)
            
            logger.info(f"Stored alert: {alert_id}")
            return alert_id
            
        except DuplicateKeyError:
            logger.warning(f"Alert already exists: {alert_id}")
            return alert_id
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
            return None
    
    def _add_alert_history(self, alert_id: str, action: str, data: Dict):
        """Add entry to alert history."""
        try:
            history_doc = {
                'alert_id': alert_id,
                'timestamp': datetime.now(timezone.utc),
                'action': action,
                'data': data
            }
            self.db.alert_history.insert_one(history_doc)
        except Exception as e:
            logger.error(f"Error adding alert history: {e}")
    
    def _store_jira_ticket(self, alert_id: str, jira_result: Dict):
        """Store JIRA ticket information."""
        try:
            ticket_doc = {
                'alert_id': alert_id,
                'ticket_key': jira_result.get('ticket_key'),
                'ticket_url': jira_result.get('ticket_url'),
                'ticket_id': jira_result.get('ticket_id'),
                'created_at': datetime.now(timezone.utc),
                'status': 'open'
            }
            self.db.jira_tickets.insert_one(ticket_doc)
        except Exception as e:
            logger.error(f"Error storing JIRA ticket: {e}")
    
    def get_alerts(self, limit: int = 50, severity: str = None, status: str = None) -> List[Dict]:
        """
        Retrieve alerts from database.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity
            status: Filter by status
            
        Returns:
            List of alerts
        """
        if not self.is_connected():
            return []
        
        try:
            query = {}
            if severity:
                query['severity'] = severity
            if status:
                query['status'] = status
            
            cursor = self.db.alerts.find(query).sort('timestamp', DESCENDING).limit(limit)
            alerts = []
            
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                if 'timestamp' in doc:
                    doc['timestamp'] = doc['timestamp'].isoformat()
                alerts.append(doc)
            
            return alerts
        except Exception as e:
            logger.error(f"Error retrieving alerts: {e}")
            return []
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Dict]:
        """Get specific alert by ID."""
        if not self.is_connected():
            return None
        
        try:
            doc = self.db.alerts.find_one({'alert_id': alert_id})
            if doc:
                doc['_id'] = str(doc['_id'])
                if 'timestamp' in doc:
                    doc['timestamp'] = doc['timestamp'].isoformat()
            return doc
        except Exception as e:
            logger.error(f"Error retrieving alert {alert_id}: {e}")
            return None
    
    def get_alert_history(self, alert_id: str) -> List[Dict]:
        """Get history for specific alert."""
        if not self.is_connected():
            return []
        
        try:
            cursor = self.db.alert_history.find({'alert_id': alert_id}).sort('timestamp', DESCENDING)
            history = []
            
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                if 'timestamp' in doc:
                    doc['timestamp'] = doc['timestamp'].isoformat()
                history.append(doc)
            
            return history
        except Exception as e:
            logger.error(f"Error retrieving alert history: {e}")
            return []
    
    def store_system_metrics(self, metrics: Dict, hostname: str = None):
        """Store system metrics."""
        if not self.is_connected():
            return
        
        try:
            metrics_doc = {
                'timestamp': datetime.now(timezone.utc),
                'hostname': hostname or os.uname().nodename,
                'metrics': metrics,
                'metric_type': 'system_status'
            }
            
            self.db.system_metrics.insert_one(metrics_doc)
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")
    
    def get_system_metrics(self, hours: int = 24, hostname: str = None) -> List[Dict]:
        """Get system metrics for specified time period."""
        if not self.is_connected():
            return []
        
        try:
            query = {
                'timestamp': {
                    '$gte': datetime.now(timezone.utc) - timedelta(hours=hours)
                }
            }
            
            if hostname:
                query['hostname'] = hostname
            
            cursor = self.db.system_metrics.find(query).sort('timestamp', DESCENDING)
            metrics = []
            
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                if 'timestamp' in doc:
                    doc['timestamp'] = doc['timestamp'].isoformat()
                metrics.append(doc)
            
            return metrics
        except Exception as e:
            logger.error(f"Error retrieving system metrics: {e}")
            return []
    
    def get_alert_stats(self) -> Dict:
        """Get alert statistics."""
        if not self.is_connected():
            return {}
        
        try:
            stats = {}
            
            # Total alerts
            stats['total_alerts'] = self.db.alerts.count_documents({})
            
            # Alerts by severity
            pipeline = [
                {'$group': {'_id': '$severity', 'count': {'$sum': 1}}}
            ]
            severity_counts = list(self.db.alerts.aggregate(pipeline))
            stats['by_severity'] = {item['_id']: item['count'] for item in severity_counts}
            
            # Alerts by status
            pipeline = [
                {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
            ]
            status_counts = list(self.db.alerts.aggregate(pipeline))
            stats['by_status'] = {item['_id']: item['count'] for item in status_counts}
            
            # Recent alerts (last 24 hours)
            recent_query = {
                'timestamp': {
                    '$gte': datetime.now(timezone.utc) - timedelta(hours=24)
                }
            }
            stats['recent_24h'] = self.db.alerts.count_documents(recent_query)
            
            # JIRA tickets created
            stats['jira_tickets'] = self.db.jira_tickets.count_documents({})
            
            return stats
        except Exception as e:
            logger.error(f"Error getting alert stats: {e}")
            return {}
    
    def update_alert_status(self, alert_id: str, status: str, metadata: Dict = None):
        """Update alert status."""
        if not self.is_connected():
            return False
        
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now(timezone.utc)
            }
            
            if metadata:
                update_data['metadata'] = metadata
            
            result = self.db.alerts.update_one(
                {'alert_id': alert_id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                self._add_alert_history(alert_id, f'status_changed_to_{status}', update_data)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection closed")