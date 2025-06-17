#!/usr/bin/env python3
"""
SQLite-based NoSQL storage for alerts and metadata using JSON fields.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SQLiteAlertStore:
    """
    SQLite-based storage with JSON fields for NoSQL-like functionality.
    """
    
    def __init__(self, db_path="alerts.db"):
        """Initialize the SQLite alert store."""
        self.db_path = db_path
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish SQLite connection and create tables."""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            logger.info(f"Connected to SQLite database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            self.connection = None
    
    def _create_tables(self):
        """Create database tables."""
        if not self.connection:
            return
        
        cursor = self.connection.cursor()
        
        # Alerts table with JSON fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alertname TEXT NOT NULL,
                instance TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                labels TEXT NOT NULL,  -- JSON
                annotations TEXT NOT NULL,  -- JSON
                starts_at TEXT,
                ends_at TEXT,
                raw_alert_data TEXT NOT NULL,  -- JSON
                jira_data TEXT,  -- JSON
                processed BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alert history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                data TEXT,  -- JSON
                FOREIGN KEY (alert_id) REFERENCES alerts (alert_id)
            )
        ''')
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                hostname TEXT NOT NULL,
                metrics TEXT NOT NULL,  -- JSON
                metric_type TEXT DEFAULT 'system_status'
            )
        ''')
        
        # JIRA tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jira_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                ticket_key TEXT UNIQUE,
                ticket_url TEXT,
                ticket_id TEXT,
                status TEXT DEFAULT 'open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES alerts (alert_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_alertname ON alerts (alertname)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_instance ON alerts (instance)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_alert_id ON alert_history (alert_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_alert_id ON jira_tickets (alert_id)')
        
        self.connection.commit()
    
    def is_connected(self):
        """Check if database is connected."""
        return self.connection is not None
    
    def store_alert(self, alert_data: Dict, jira_result: Optional[Dict] = None) -> Optional[str]:
        """Store an alert in the database."""
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
            
            cursor = self.connection.cursor()
            
            # Insert alert
            cursor.execute('''
                INSERT OR REPLACE INTO alerts 
                (alert_id, alertname, instance, severity, status, labels, annotations, 
                 starts_at, ends_at, raw_alert_data, jira_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_id,
                labels.get('alertname', 'unknown'),
                labels.get('instance', 'unknown'),
                labels.get('severity', 'unknown'),
                alert_data.get('status', 'firing'),
                json.dumps(labels),
                json.dumps(primary_alert.get('annotations', {})),
                primary_alert.get('startsAt'),
                primary_alert.get('endsAt'),
                json.dumps(alert_data),
                json.dumps(jira_result) if jira_result else None
            ))
            
            # Add to history
            self._add_alert_history(alert_id, 'created', {'alert_data': alert_data})
            
            # Store JIRA ticket if created successfully
            if jira_result and jira_result.get('success'):
                cursor.execute('''
                    INSERT INTO jira_tickets (alert_id, ticket_key, ticket_url, ticket_id)
                    VALUES (?, ?, ?, ?)
                ''', (
                    alert_id,
                    jira_result.get('ticket_key'),
                    jira_result.get('ticket_url'),
                    jira_result.get('ticket_id')
                ))
            
            self.connection.commit()
            logger.info(f"Stored alert: {alert_id}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def _add_alert_history(self, alert_id: str, action: str, data: Dict):
        """Add entry to alert history."""
        if not self.is_connected():
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO alert_history (alert_id, action, data)
                VALUES (?, ?, ?)
            ''', (alert_id, action, json.dumps(data)))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error adding alert history: {e}")
    
    def get_alerts(self, limit: int = 50, severity: str = None, status: str = None) -> List[Dict]:
        """Retrieve alerts from database."""
        if not self.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT * FROM alerts"
            params = []
            where_clauses = []
            
            if severity:
                where_clauses.append("severity = ?")
                params.append(severity)
            
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alert = dict(row)
                # Parse JSON fields
                alert['labels'] = json.loads(alert['labels'])
                alert['annotations'] = json.loads(alert['annotations'])
                alert['raw_alert_data'] = json.loads(alert['raw_alert_data'])
                if alert['jira_data']:
                    alert['jira_data'] = json.loads(alert['jira_data'])
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error retrieving alerts: {e}")
            return []
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Dict]:
        """Get specific alert by ID."""
        if not self.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
            row = cursor.fetchone()
            
            if row:
                alert = dict(row)
                alert['labels'] = json.loads(alert['labels'])
                alert['annotations'] = json.loads(alert['annotations'])
                alert['raw_alert_data'] = json.loads(alert['raw_alert_data'])
                if alert['jira_data']:
                    alert['jira_data'] = json.loads(alert['jira_data'])
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving alert {alert_id}: {e}")
            return None
    
    def get_alert_history(self, alert_id: str) -> List[Dict]:
        """Get history for specific alert."""
        if not self.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM alert_history 
                WHERE alert_id = ? 
                ORDER BY timestamp DESC
            ''', (alert_id,))
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                entry = dict(row)
                if entry['data']:
                    entry['data'] = json.loads(entry['data'])
                history.append(entry)
            
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving alert history: {e}")
            return []
    
    def store_system_metrics(self, metrics: Dict, hostname: str = None):
        """Store system metrics."""
        if not self.is_connected():
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO system_metrics (hostname, metrics)
                VALUES (?, ?)
            ''', (
                hostname or os.uname().nodename,
                json.dumps(metrics)
            ))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")
    
    def get_system_metrics(self, hours: int = 24, hostname: str = None) -> List[Dict]:
        """Get system metrics for specified time period."""
        if not self.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = '''
                SELECT * FROM system_metrics 
                WHERE timestamp >= datetime('now', '-{} hours')
            '''.format(hours)
            
            params = []
            if hostname:
                query += " AND hostname = ?"
                params.append(hostname)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            metrics = []
            for row in rows:
                entry = dict(row)
                entry['metrics'] = json.loads(entry['metrics'])
                metrics.append(entry)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving system metrics: {e}")
            return []
    
    def get_alert_stats(self) -> Dict:
        """Get alert statistics."""
        if not self.is_connected():
            return {}
        
        try:
            cursor = self.connection.cursor()
            stats = {}
            
            # Total alerts
            cursor.execute("SELECT COUNT(*) FROM alerts")
            stats['total_alerts'] = cursor.fetchone()[0]
            
            # Alerts by severity
            cursor.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
            stats['by_severity'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Alerts by status
            cursor.execute("SELECT status, COUNT(*) FROM alerts GROUP BY status")
            stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Recent alerts (last 24 hours)
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp >= datetime('now', '-24 hours')")
            stats['recent_24h'] = cursor.fetchone()[0]
            
            # JIRA tickets
            cursor.execute("SELECT COUNT(*) FROM jira_tickets")
            stats['jira_tickets'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert stats: {e}")
            return {}
    
    def update_alert_status(self, alert_id: str, status: str, metadata: Dict = None) -> bool:
        """Update alert status."""
        if not self.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE alert_id = ?
            ''', (status, alert_id))
            
            if cursor.rowcount > 0:
                update_data = {'status': status}
                if metadata:
                    update_data['metadata'] = metadata
                
                self._add_alert_history(alert_id, f'status_changed_to_{status}', update_data)
                self.connection.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
            return False
    
    def get_existing_jira_ticket(self, alert_signature: str) -> Optional[Dict]:
        """
        Check if JIRA ticket already exists for similar alert.
        
        Args:
            alert_signature: Unique signature identifying similar alerts (alertname_instance)
            
        Returns:
            Existing ticket information or None
        """
        if not self.is_connected():
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT jt.ticket_key, jt.ticket_url, jt.status, jt.created_at, a.alert_id
                FROM jira_tickets jt
                JOIN alerts a ON jt.alert_id = a.alert_id
                WHERE a.alertname || '_' || a.instance = ?
                AND jt.status != 'resolved'
                ORDER BY jt.created_at DESC
                LIMIT 1
            ''', (alert_signature,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'ticket_key': result[0],
                    'ticket_url': result[1],
                    'status': result[2],
                    'created_at': result[3],
                    'alert_id': result[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing JIRA tickets: {str(e)}")
            return None
    
    def check_ticket_exists_for_alert(self, alertname: str, instance: str) -> Optional[Dict]:
        """
        Check if open JIRA ticket exists for specific alert and instance.
        
        Args:
            alertname: Alert name
            instance: Instance identifier
            
        Returns:
            Existing ticket info or None
        """
        alert_signature = f"{alertname}_{instance}"
        return self.get_existing_jira_ticket(alert_signature)

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("SQLite connection closed")