import os
import json
import smtplib
import logging
import requests
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from datetime import datetime
from .config.config import CONFIG

class AlertManager:
    """Manages system alerts and notifications"""
    
    SEVERITY_LEVELS = {
        'CRITICAL': 50,
        'ERROR': 40,
        'WARNING': 30,
        'INFO': 20,
        'DEBUG': 10
    }
    
    def __init__(self):
        self.logger = logging.getLogger('RootBot.AlertManager')
        self.alerts_log = os.path.join(CONFIG['LOG_DIR'], 'alerts.log')
        self.notification_config = CONFIG.get('NOTIFICATIONS', {})
        
    def send_alert(self, 
                   message: str, 
                   severity: str = 'INFO', 
                   context: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert through configured channels"""
        try:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'severity': severity,
                'message': message,
                'context': context or {}
            }
            
            # Log the alert
            self._log_alert(alert)
            
            # Send notifications based on severity
            if self.SEVERITY_LEVELS.get(severity, 0) >= self.SEVERITY_LEVELS['WARNING']:
                self._send_notifications(alert)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")
            return False
            
    def _log_alert(self, alert: Dict[str, Any]):
        """Log alert to file"""
        try:
            with open(self.alerts_log, 'a') as f:
                f.write(json.dumps(alert) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to log alert: {str(e)}")
            
    def _send_notifications(self, alert: Dict[str, Any]):
        """Send notifications through configured channels"""
        if 'email' in self.notification_config:
            self._send_email_alert(alert)
            
        if 'slack' in self.notification_config:
            self._send_slack_alert(alert)
            
        if 'telegram' in self.notification_config:
            self._send_telegram_alert(alert)
            
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send alert via email"""
        try:
            config = self.notification_config['email']
            msg = MIMEText(
                f"Severity: {alert['severity']}\n"
                f"Message: {alert['message']}\n"
                f"Context: {json.dumps(alert['context'], indent=2)}"
            )
            
            msg['Subject'] = f"RootBot Alert: {alert['severity']}"
            msg['From'] = config['from']
            msg['To'] = config['to']
            
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                if config.get('use_tls'):
                    server.starttls()
                if 'username' in config:
                    server.login(config['username'], config['password'])
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")
            
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send alert via Slack"""
        try:
            config = self.notification_config['slack']
            payload = {
                'text': (
                    f"*RootBot Alert*\n"
                    f"*Severity*: {alert['severity']}\n"
                    f"*Message*: {alert['message']}\n"
                    f"*Context*: ```{json.dumps(alert['context'], indent=2)}```"
                )
            }
            
            requests.post(config['webhook_url'], json=payload)
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")
            
    def _send_telegram_alert(self, alert: Dict[str, Any]):
        """Send alert via Telegram"""
        try:
            config = self.notification_config['telegram']
            message = (
                f"🤖 *RootBot Alert*\n"
                f"*Severity*: {alert['severity']}\n"
                f"*Message*: {alert['message']}\n"
                f"*Context*: ```{json.dumps(alert['context'], indent=2)}```"
            )
            
            payload = {
                'chat_id': config['chat_id'],
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            requests.post(
                f"https://api.telegram.org/bot{config['bot_token']}/sendMessage",
                json=payload
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {str(e)}")
            
    def get_recent_alerts(self, 
                         severity: Optional[str] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alerts with optional filtering"""
        try:
            alerts = []
            with open(self.alerts_log, 'r') as f:
                for line in f.readlines()[-limit:]:
                    alert = json.loads(line)
                    if severity is None or alert['severity'] == severity:
                        alerts.append(alert)
            return alerts
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {str(e)}")
            return []
