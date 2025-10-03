"""Notification service for alerts and webhooks."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import httpx

from ..config import settings
from ..models.alert import Alert, Notification, NotificationChannel

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications and webhooks."""
    
    def __init__(self):
        self.slack_webhook_url = settings.slack_webhook_url
        self.crm_webhook_url = settings.crm_webhook_url
        self.webhook_secret = settings.webhook_secret
        self._http_client = httpx.AsyncClient(timeout=30.0)
    
    async def send_alert_notifications(self, alerts: List[Alert]) -> List[Notification]:
        """Send notifications for alerts."""
        notifications = []
        
        for alert in alerts:
            # Send to dashboard (always)
            dashboard_notification = await self._send_dashboard_notification(alert)
            if dashboard_notification:
                notifications.append(dashboard_notification)
            
            # Send to Slack if configured
            if self.slack_webhook_url:
                slack_notification = await self._send_slack_notification(alert)
                if slack_notification:
                    notifications.append(slack_notification)
            
            # Send to CRM if configured
            if self.crm_webhook_url:
                crm_notification = await self._send_crm_notification(alert)
                if crm_notification:
                    notifications.append(crm_notification)
        
        return notifications
    
    async def _send_dashboard_notification(self, alert: Alert) -> Optional[Notification]:
        """Send notification to dashboard."""
        try:
            # In a real implementation, this would update a database or send to a real-time system
            notification = Notification(
                notification_id=f"dashboard_{alert.alert_id}",
                alert_id=alert.alert_id,
                channel=NotificationChannel.DASHBOARD,
                recipient="dashboard",
                message=f"Alert: {alert.title} - {alert.description}",
                status="sent"
            )
            
            logger.info(f"Dashboard notification sent for alert {alert.alert_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error sending dashboard notification: {e}")
            return None
    
    async def _send_slack_notification(self, alert: Alert) -> Optional[Notification]:
        """Send notification to Slack."""
        try:
            # Create Slack message
            slack_message = self._create_slack_message(alert)
            
            # Send to Slack webhook
            response = await self._http_client.post(
                self.slack_webhook_url,
                json=slack_message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                notification = Notification(
                    notification_id=f"slack_{alert.alert_id}",
                    alert_id=alert.alert_id,
                    channel=NotificationChannel.SLACK,
                    recipient="slack_channel",
                    message=slack_message["text"],
                    status="sent"
                )
                
                logger.info(f"Slack notification sent for alert {alert.alert_id}")
                return notification
            else:
                logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return None
    
    async def _send_crm_notification(self, alert: Alert) -> Optional[Notification]:
        """Send notification to CRM system."""
        try:
            # Create CRM payload
            crm_payload = self._create_crm_payload(alert)
            
            # Send to CRM webhook
            headers = {"Content-Type": "application/json"}
            if self.webhook_secret:
                headers["Authorization"] = f"Bearer {self.webhook_secret}"
            
            response = await self._http_client.post(
                self.crm_webhook_url,
                json=crm_payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                notification = Notification(
                    notification_id=f"crm_{alert.alert_id}",
                    alert_id=alert.alert_id,
                    channel=NotificationChannel.WEBHOOK,
                    recipient="crm_system",
                    message=f"CRM task created for alert {alert.alert_id}",
                    status="sent"
                )
                
                logger.info(f"CRM notification sent for alert {alert.alert_id}")
                return notification
            else:
                logger.error(f"CRM webhook failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending CRM notification: {e}")
            return None
    
    def _create_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Create Slack message format."""
        # Determine color based on severity
        color_map = {
            "LOW": "#36a64f",      # Green
            "MEDIUM": "#ffaa00",   # Yellow
            "HIGH": "#ff6600",     # Orange
            "CRITICAL": "#ff0000"  # Red
        }
        
        color = color_map.get(alert.severity.value, "#36a64f")
        
        # Create attachment
        attachment = {
            "color": color,
            "title": alert.title,
            "text": alert.description,
            "fields": [
                {
                    "title": "Severity",
                    "value": alert.severity.value,
                    "short": True
                },
                {
                    "title": "Type",
                    "value": alert.type.value,
                    "short": True
                }
            ],
            "footer": "Financial Contract Drift Monitor",
            "ts": int(alert.created_at.timestamp())
        }
        
        # Add contract info if available
        if alert.contract_id:
            attachment["fields"].append({
                "title": "Contract ID",
                "value": alert.contract_id,
                "short": True
            })
        
        # Add rule info if available
        if alert.rule_id:
            attachment["fields"].append({
                "title": "Rule ID",
                "value": alert.rule_id,
                "short": True
            })
        
        return {
            "text": f"🚨 Contract Alert: {alert.title}",
            "attachments": [attachment]
        }
    
    def _create_crm_payload(self, alert: Alert) -> Dict[str, Any]:
        """Create CRM webhook payload."""
        return {
            "event_type": "contract_alert",
            "alert_id": alert.alert_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "type": alert.type.value,
            "contract_id": alert.contract_id,
            "rule_id": alert.rule_id,
            "created_at": alert.created_at.isoformat(),
            "details": alert.details,
            "action_required": self._determine_crm_action(alert)
        }
    
    def _determine_crm_action(self, alert: Alert) -> str:
        """Determine required CRM action based on alert."""
        if alert.severity.value in ["HIGH", "CRITICAL"]:
            return "URGENT_REVIEW"
        elif alert.type.value == "rule_violation":
            return "COMPLIANCE_CHECK"
        elif alert.type.value == "drift_detected":
            return "CONTRACT_REVIEW"
        else:
            return "INVESTIGATE"
    
    async def send_webhook(self, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
        """Send generic webhook."""
        try:
            default_headers = {"Content-Type": "application/json"}
            if headers:
                default_headers.update(headers)
            
            response = await self._http_client.post(url, json=payload, headers=default_headers)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook sent successfully to {url}")
                return True
            else:
                logger.error(f"Webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook to {url}: {e}")
            return False
    
    async def send_batch_notifications(self, alerts: List[Alert], batch_size: int = 10) -> List[Notification]:
        """Send notifications in batches."""
        all_notifications = []
        
        for i in range(0, len(alerts), batch_size):
            batch = alerts[i:i + batch_size]
            batch_notifications = await self.send_alert_notifications(batch)
            all_notifications.extend(batch_notifications)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        return all_notifications
    
    async def test_notification_channels(self) -> Dict[str, bool]:
        """Test all notification channels."""
        results = {}
        
        # Test Slack
        if self.slack_webhook_url:
            test_alert = Alert(
                alert_id="test_alert",
                type="system_error",
                severity="LOW",
                title="Test Alert",
                description="This is a test notification"
            )
            slack_notification = await self._send_slack_notification(test_alert)
            results["slack"] = slack_notification is not None
        else:
            results["slack"] = False
        
        # Test CRM
        if self.crm_webhook_url:
            test_alert = Alert(
                alert_id="test_alert",
                type="system_error",
                severity="LOW",
                title="Test Alert",
                description="This is a test notification"
            )
            crm_notification = await self._send_crm_notification(test_alert)
            results["crm"] = crm_notification is not None
        else:
            results["crm"] = False
        
        # Dashboard is always available
        results["dashboard"] = True
        
        return results
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            asyncio.create_task(self.close())
        except:
            pass
