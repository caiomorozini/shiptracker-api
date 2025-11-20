"""
ShipTracker SSW Sync DAG

Synchronizes tracking data from SSW system with ShipTracker API.
Runs every 15 minutes to check for updates on active shipments.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.exceptions import AirflowException
from dotenv import load_dotenv

from utils.api_client import ShipTrackerAPIClient
from utils.ssw_client import SSWClient
from utils.ssw_parser import SSWParser

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DAG_ID = "shiptracker_ssw_sync"
SCHEDULE_INTERVAL = "*/15 * * * *"  # Every 15 minutes
MAX_FAILURE_THRESHOLD = 0.3  # Alert if >30% of shipments fail

DEFAULT_ARGS = {
    "owner": "shiptracker",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


class ShipmentProcessingResult:
    """Data class for shipment processing results"""
    
    def __init__(
        self,
        shipment_id: str,
        tracking_code: str,
        success: bool,
        new_event_created: bool = False,
        error_message: Optional[str] = None
    ):
        self.shipment_id = shipment_id
        self.tracking_code = tracking_code
        self.success = success
        self.new_event_created = new_event_created
        self.error_message = error_message
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for XCom storage"""
        return {
            "shipment_id": self.shipment_id,
            "tracking_code": self.tracking_code,
            "success": self.success,
            "new_event": self.new_event_created,
            "error": self.error_message,
        }


class ShipmentProcessor:
    """Handles the processing of individual shipments"""
    
    def __init__(
        self,
        api_client: ShipTrackerAPIClient,
        ssw_client: SSWClient,
        ssw_parser: SSWParser
    ):
        self.api_client = api_client
        self.ssw_client = ssw_client
        self.ssw_parser = ssw_parser
    
    def process(self, shipment: Dict) -> ShipmentProcessingResult:
        """
        Process a single shipment by fetching SSW data and updating API
        
        Args:
            shipment: Shipment data from API
            
        Returns:
            ShipmentProcessingResult with processing outcome
        """
        shipment_id = str(shipment["id"])
        tracking_code = shipment["tracking_code"]
        
        logger.info(f"Processing shipment {shipment_id} - {tracking_code}")
        
        try:
            # Fetch and parse SSW data
            tracking_data = self._fetch_tracking_data(shipment)
            if not tracking_data:
                return ShipmentProcessingResult(
                    shipment_id, tracking_code, False,
                    error_message="Failed to fetch or parse SSW data"
                )
            
            # Check if update is needed
            if not self._should_create_event(shipment_id, tracking_data):
                logger.info(f"No new updates for shipment {shipment_id}")
                return ShipmentProcessingResult(shipment_id, tracking_code, True)
            
            # Create event and update shipment
            event_created = self._create_tracking_event(shipment_id, tracking_data)
            if not event_created:
                return ShipmentProcessingResult(
                    shipment_id, tracking_code, False,
                    error_message="Failed to create tracking event"
                )
            
            self._update_shipment_status(shipment_id, tracking_data)
            self._send_notification(shipment, tracking_data)
            
            logger.info(f"Successfully processed shipment {shipment_id}")
            return ShipmentProcessingResult(
                shipment_id, tracking_code, True, new_event_created=True
            )
            
        except Exception as e:
            logger.error(f"Error processing shipment {shipment_id}: {e}", exc_info=True)
            return ShipmentProcessingResult(
                shipment_id, tracking_code, False, error_message=str(e)
            )
    
    def _fetch_tracking_data(self, shipment: Dict) -> Optional[Dict]:
        """Fetch and parse tracking data from SSW"""
        client_data = shipment.get("client", {})
        cpf_cnpj = client_data.get("cpf_cnpj", "")
        invoice_number = str(shipment["invoice_number"])
        
        html_content = self.ssw_client.get_tracking_html(cpf_cnpj, invoice_number)
        if not html_content:
            return None
        
        return self.ssw_parser.parse_tracking_html(html_content)
    
    def _should_create_event(self, shipment_id: str, tracking_data: Dict) -> bool:
        """Check if a new tracking event should be created"""
        events = self.api_client.get_shipment_events(shipment_id)
        last_event = events[0] if events else None
        
        if not last_event:
            return True
        
        return self.ssw_parser.has_new_update(tracking_data, last_event)
    
    def _create_tracking_event(self, shipment_id: str, tracking_data: Dict) -> bool:
        """Create a new tracking event"""
        try:
            event = self.api_client.create_tracking_event(
                shipment_id=shipment_id,
                status=tracking_data["status"],
                description=tracking_data["description"],
                location=tracking_data["location"],
                occurred_at=datetime.fromisoformat(tracking_data["datetime"]),
            )
            return event is not None
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return False
    
    def _update_shipment_status(self, shipment_id: str, tracking_data: Dict) -> None:
        """Update shipment status and location"""
        update_data = {
            "status": tracking_data["status"],
            "current_location": tracking_data["location"],
        }
        
        if self.ssw_parser.is_delivered(tracking_data):
            update_data["delivered_at"] = tracking_data["datetime"]
            logger.info(f"Shipment {shipment_id} marked as delivered")
        
        self.api_client.update_shipment(shipment_id, update_data)
    
    def _send_notification(self, shipment: Dict, tracking_data: Dict) -> None:
        """Send notification to client about status update"""
        client_data = shipment.get("client", {})
        client_user_id = client_data.get("user_id")
        
        if not client_user_id:
            return
        
        tracking_code = shipment["tracking_code"]
        title = f"Atualização de Rastreamento - {tracking_code}"
        message = (
            f"Status: {tracking_data['status']}\n"
            f"Localização: {tracking_data['location']}\n"
            f"Data/Hora: {tracking_data['datetime']}"
        )
        
        try:
            self.api_client.create_notification(
                user_id=client_user_id,
                title=title,
                message=message,
                notification_type="shipment_update",
                related_shipment_id=shipment["id"],
            )
            logger.info(f"Notification sent to user {client_user_id}")
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")


class ProcessingSummary:
    """Summary of batch processing results"""
    
    def __init__(self, results: List[ShipmentProcessingResult]):
        self.results = results
        self.total_processed = len(results)
        self.total_success = sum(1 for r in results if r.success)
        self.total_failed = self.total_processed - self.total_success
        self.total_new_events = sum(1 for r in results if r.new_event_created)
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage"""
        if self.total_processed == 0:
            return 0.0
        return self.total_failed / self.total_processed
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for XCom storage"""
        return {
            "processed": self.total_processed,
            "success": self.total_success,
            "failed": self.total_failed,
            "new_events": self.total_new_events,
            "results": [r.to_dict() for r in self.results],
        }
    
    def log_summary(self) -> None:
        """Log processing summary"""
        logger.info(
            f"Processing complete - "
            f"Processed: {self.total_processed}, "
            f"Success: {self.total_success}, "
            f"Failed: {self.total_failed}, "
            f"New Events: {self.total_new_events}"
        )


def fetch_and_process_shipments(**context) -> Dict:
    """
    Main task: Fetch active shipments from API and process each one
    
    Returns:
        Dictionary with processing summary
    """
    logger.info("Starting SSW tracking update process")
    
    # Initialize clients
    api_client = ShipTrackerAPIClient()
    ssw_client = SSWClient()
    ssw_parser = SSWParser()
    processor = ShipmentProcessor(api_client, ssw_client, ssw_parser)
    
    try:
        # Fetch active shipments
        active_shipments = api_client.get_active_shipments()
        
        if not active_shipments:
            logger.info("No active shipments to process")
            return {"processed": 0, "success": 0, "failed": 0, "new_events": 0}
        
        logger.info(f"Found {len(active_shipments)} active shipments")
        
        # Process each shipment
        results = [processor.process(shipment) for shipment in active_shipments]
        
        # Generate summary
        summary = ProcessingSummary(results)
        summary.log_summary()
        
        # Store in XCom for monitoring
        context["ti"].xcom_push(key="summary", value=summary.to_dict())
        
        # Alert if failure rate is too high
        if summary.failure_rate > MAX_FAILURE_THRESHOLD:
            logger.warning(
                f"High failure rate: {summary.total_failed}/{summary.total_processed} "
                f"({summary.failure_rate:.1%}) shipments failed"
            )
        
        return summary.to_dict()
        
    except Exception as e:
        logger.error(f"Critical error in tracking process: {e}", exc_info=True)
        raise AirflowException(f"Tracking process failed: {e}")


# Create DAG
with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="Sync tracking updates from SSW system to ShipTracker API",
    schedule=SCHEDULE_INTERVAL,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["shiptracker", "ssw", "tracking"],
    max_active_runs=1,
) as dag:
    
    process_task = PythonOperator(
        task_id="process_shipments",
        python_callable=fetch_and_process_shipments,
    )
