"""Webhook handlers for external system integrations."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import hashlib
import hmac

from fastapi import HTTPException, Request
from ..config import settings
from ..models.alert import Alert, AlertType, AlertSeverity
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handler for incoming webhooks from external systems."""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.webhook_secret = settings.webhook_secret
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature for security."""
        if not secret:
            logger.warning("No webhook secret configured")
            return True  # Allow if no secret is configured
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_crm_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle webhook from CRM system."""
        try:
            payload = await request.body()
            signature = request.headers.get("X-Signature", "")
            
            # Verify signature
            if not self.verify_webhook_signature(payload, signature, self.webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            data = json.loads(payload)
            
            # Process CRM event
            if data.get("event_type") == "task_created":
                return await self._handle_crm_task_created(data)
            elif data.get("event_type") == "task_updated":
                return await self._handle_crm_task_updated(data)
            elif data.get("event_type") == "task_completed":
                return await self._handle_crm_task_completed(data)
            else:
                logger.warning(f"Unknown CRM event type: {data.get('event_type')}")
                return {"status": "ignored", "reason": "unknown_event_type"}
                
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            logger.error(f"Error handling CRM webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def handle_portfolio_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle webhook from portfolio management system."""
        try:
            payload = await request.body()
            signature = request.headers.get("X-Signature", "")
            
            # Verify signature
            if not self.verify_webhook_signature(payload, signature, self.webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            data = json.loads(payload)
            
            # Process portfolio event
            if data.get("event_type") == "trade_executed":
                return await self._handle_trade_executed(data)
            elif data.get("event_type") == "fee_calculated":
                return await self._handle_fee_calculated(data)
            elif data.get("event_type") == "allocation_made":
                return await self._handle_allocation_made(data)
            else:
                logger.warning(f"Unknown portfolio event type: {data.get('event_type')}")
                return {"status": "ignored", "reason": "unknown_event_type"}
                
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            logger.error(f"Error handling portfolio webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def handle_fund_admin_webhook(self, request: Request) -> Dict[str, Any]:
        """Handle webhook from fund administration system."""
        try:
            payload = await request.body()
            signature = request.headers.get("X-Signature", "")
            
            # Verify signature
            if not self.verify_webhook_signature(payload, signature, self.webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            data = json.loads(payload)
            
            # Process fund admin event
            if data.get("event_type") == "capital_call":
                return await self._handle_capital_call(data)
            elif data.get("event_type") == "distribution":
                return await self._handle_distribution(data)
            elif data.get("event_type") == "report_generated":
                return await self._handle_report_generated(data)
            else:
                logger.warning(f"Unknown fund admin event type: {data.get('event_type')}")
                return {"status": "ignored", "reason": "unknown_event_type"}
                
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            logger.error(f"Error handling fund admin webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _handle_crm_task_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CRM task created event."""
        logger.info(f"CRM task created: {data.get('task_id')}")
        
        # Create alert for new CRM task
        alert = Alert(
            alert_id=f"crm_task_{data.get('task_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.MEDIUM,
            title=f"CRM Task Created: {data.get('title', 'Unknown')}",
            description=data.get("description", ""),
            contract_id=data.get("contract_id"),
            details={
                "task_id": data.get("task_id"),
                "assigned_to": data.get("assigned_to"),
                "due_date": data.get("due_date"),
                "priority": data.get("priority")
            }
        )
        
        # Send notification
        await self.notification_service.send_alert_notifications([alert])
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_crm_task_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CRM task updated event."""
        logger.info(f"CRM task updated: {data.get('task_id')}")
        
        # Update existing alert or create new one
        alert = Alert(
            alert_id=f"crm_task_update_{data.get('task_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.LOW,
            title=f"CRM Task Updated: {data.get('title', 'Unknown')}",
            description=f"Task status changed to: {data.get('status', 'Unknown')}",
            contract_id=data.get("contract_id"),
            details={
                "task_id": data.get("task_id"),
                "status": data.get("status"),
                "updated_by": data.get("updated_by"),
                "updated_at": data.get("updated_at")
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_crm_task_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CRM task completed event."""
        logger.info(f"CRM task completed: {data.get('task_id')}")
        
        # Create completion alert
        alert = Alert(
            alert_id=f"crm_task_completed_{data.get('task_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.LOW,
            title=f"CRM Task Completed: {data.get('title', 'Unknown')}",
            description=f"Task completed by: {data.get('completed_by', 'Unknown')}",
            contract_id=data.get("contract_id"),
            details={
                "task_id": data.get("task_id"),
                "completed_by": data.get("completed_by"),
                "completed_at": data.get("completed_at"),
                "notes": data.get("notes")
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_trade_executed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle trade executed event from portfolio system."""
        logger.info(f"Trade executed: {data.get('trade_id')}")
        
        # Validate trade against contract rules
        # This would integrate with the validation engine
        
        alert = Alert(
            alert_id=f"trade_{data.get('trade_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.MEDIUM,
            title=f"Trade Executed: {data.get('symbol', 'Unknown')}",
            description=f"Trade executed for {data.get('quantity', 0)} shares at ${data.get('price', 0)}",
            contract_id=data.get("contract_id"),
            details={
                "trade_id": data.get("trade_id"),
                "symbol": data.get("symbol"),
                "quantity": data.get("quantity"),
                "price": data.get("price"),
                "executed_at": data.get("executed_at")
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_fee_calculated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fee calculated event from portfolio system."""
        logger.info(f"Fee calculated: {data.get('fee_id')}")
        
        # Validate fee calculation against contract rules
        # This would integrate with the validation engine
        
        alert = Alert(
            alert_id=f"fee_{data.get('fee_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.HIGH,
            title=f"Fee Calculated: {data.get('fee_type', 'Unknown')}",
            description=f"Fee calculated: ${data.get('amount', 0)} for {data.get('period', 'Unknown')}",
            contract_id=data.get("contract_id"),
            details={
                "fee_id": data.get("fee_id"),
                "fee_type": data.get("fee_type"),
                "amount": data.get("amount"),
                "period": data.get("period"),
                "calculated_at": data.get("calculated_at")
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_allocation_made(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle allocation made event from portfolio system."""
        logger.info(f"Allocation made: {data.get('allocation_id')}")
        
        # Validate allocation against contract restrictions
        # This would integrate with the validation engine
        
        alert = Alert(
            alert_id=f"allocation_{data.get('allocation_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.MEDIUM,
            title=f"Allocation Made: {data.get('sector', 'Unknown')}",
            description=f"Allocation of ${data.get('amount', 0)} to {data.get('sector', 'Unknown')} sector",
            contract_id=data.get("contract_id"),
            details={
                "allocation_id": data.get("allocation_id"),
                "sector": data.get("sector"),
                "amount": data.get("amount"),
                "percentage": data.get("percentage"),
                "allocated_at": data.get("allocated_at")
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_capital_call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle capital call event from fund admin system."""
        logger.info(f"Capital call: {data.get('call_id')}")
        
        alert = Alert(
            alert_id=f"capital_call_{data.get('call_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.HIGH,
            title=f"Capital Call: {data.get('call_type', 'Unknown')}",
            description=f"Capital call of ${data.get('amount', 0)} due on {data.get('due_date', 'Unknown')}",
            contract_id=data.get("contract_id"),
            details={
                "call_id": data.get("call_id"),
                "call_type": data.get("call_type"),
                "amount": data.get("amount"),
                "due_date": data.get("due_date"),
                "investors": data.get("investors", [])
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle distribution event from fund admin system."""
        logger.info(f"Distribution: {data.get('distribution_id')}")
        
        alert = Alert(
            alert_id=f"distribution_{data.get('distribution_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.MEDIUM,
            title=f"Distribution: {data.get('distribution_type', 'Unknown')}",
            description=f"Distribution of ${data.get('amount', 0)} to investors",
            contract_id=data.get("contract_id"),
            details={
                "distribution_id": data.get("distribution_id"),
                "distribution_type": data.get("distribution_type"),
                "amount": data.get("amount"),
                "distributed_at": data.get("distributed_at"),
                "investors": data.get("investors", [])
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
    
    async def _handle_report_generated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generated event from fund admin system."""
        logger.info(f"Report generated: {data.get('report_id')}")
        
        # Validate report timing against contract requirements
        # This would integrate with the validation engine
        
        alert = Alert(
            alert_id=f"report_{data.get('report_id')}",
            type=AlertType.RULE_VIOLATION,
            severity=AlertSeverity.LOW,
            title=f"Report Generated: {data.get('report_type', 'Unknown')}",
            description=f"Report generated for period {data.get('period', 'Unknown')}",
            contract_id=data.get("contract_id"),
            details={
                "report_id": data.get("report_id"),
                "report_type": data.get("report_type"),
                "period": data.get("period"),
                "generated_at": data.get("generated_at"),
                "file_path": data.get("file_path")
            }
        )
        
        return {"status": "processed", "alert_id": alert.alert_id}
