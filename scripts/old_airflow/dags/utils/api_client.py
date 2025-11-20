"""
API Client for ShipTracker API
Handles authentication and API requests
"""
import os
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ShipTrackerAPIClient:
    """Client for interacting with ShipTracker API"""

    def __init__(self):
        self.base_url = os.getenv('SHIPTRACKER_API_URL', 'http://localhost:8000')
        self.email = os.getenv('SHIPTRACKER_API_EMAIL')
        self.password = os.getenv('SHIPTRACKER_API_PASSWORD')
        self.token = None
        self.token_expires_at = None

    def _ensure_authenticated(self):
        """Ensure we have a valid token"""
        if not self.token:
            self._authenticate()

    def _authenticate(self):
        """Authenticate and get access token"""
        url = f"{self.base_url}/api/auth/login"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    data={
                        "username": self.email,
                        "password": self.password
                    }
                )
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                logger.info("Successfully authenticated with API")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        self._ensure_authenticated()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # ==================== Shipments ====================

    def get_active_shipments(self) -> List[Dict[str, Any]]:
        """Get all active shipments that need tracking"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/shipments",
                    headers=self._get_headers(),
                    params={
                        "status": "in_transit,pending",
                        "limit": 1000
                    }
                )
                response.raise_for_status()
                data = response.json()
                shipments = data.get('items', [])
                logger.info(f"Found {len(shipments)} active shipments")
                return shipments

        except Exception as e:
            logger.error(f"Failed to get active shipments: {e}")
            raise

    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict[str, Any]]:
        """Get shipment details by ID"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/shipments/{shipment_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Shipment {shipment_id} not found")
                return None
            raise

    def update_shipment(self, shipment_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update shipment information"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.patch(
                    f"{self.base_url}/api/shipments/{shipment_id}",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                logger.info(f"Updated shipment {shipment_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Failed to update shipment {shipment_id}: {e}")
            raise

    def create_tracking_event(
        self,
        shipment_id: str,
        status: str,
        description: str,
        location: Optional[str] = None,
        occurred_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a tracking event for a shipment"""
        try:
            event_data = {
                "shipment_id": shipment_id,
                "status": status,
                "description": description,
            }

            if location:
                event_data["location"] = location

            if occurred_at:
                event_data["occurred_at"] = occurred_at.isoformat()

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/api/shipments/{shipment_id}/events",
                    headers=self._get_headers(),
                    json=event_data
                )
                response.raise_for_status()
                logger.info(f"Created tracking event for shipment {shipment_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Failed to create tracking event: {e}")
            raise

    def get_shipment_events(self, shipment_id: str) -> List[Dict[str, Any]]:
        """Get all tracking events for a shipment"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/shipments/{shipment_id}/events",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get shipment events: {e}")
            raise

    # ==================== Clients ====================

    def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client details by ID"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/clients/{client_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Client {client_id} not found")
                return None
            raise

    # ==================== Notifications ====================

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        related_shipment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a notification in the system"""
        try:
            notification_data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type
            }

            if related_shipment_id:
                notification_data["related_shipment_id"] = related_shipment_id

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/api/notifications",
                    headers=self._get_headers(),
                    json=notification_data
                )
                response.raise_for_status()
                logger.info(f"Created notification for user {user_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            raise
