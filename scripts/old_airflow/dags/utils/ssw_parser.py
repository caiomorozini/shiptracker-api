"""
SSW System HTML Parser

Parses tracking HTML from SSW system and extracts structured data.
Handles Brazilian Portuguese status codes and date formats.
"""
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Status mapping from SSW (Portuguese) to system status codes (English)
STATUS_MAPPING = {
    "MERCADORIA ENTREGUE": "delivered",
    "MERCADORIA EM TRÂNSITO": "in_transit",
    "MERCADORIA SAIU PARA ENTREGA": "out_for_delivery",
    "MERCADORIA AGUARDANDO RETIRADA": "ready_for_pickup",
    "MERCADORIA POSTADA": "posted",
    "AGUARDANDO POSTAGEM": "pending",
    "ATRASO NA ENTREGA": "delayed",
    "TENTATIVA DE ENTREGA": "delivery_attempt",
    "MERCADORIA RETORNADA": "returned",
}

MIN_HTML_LENGTH = 100


class SSWParser:
    """Parser for SSW tracking system HTML responses"""

    @staticmethod
    def parse_tracking_html(html_content: str) -> Optional[Dict[str, Any]]:
        """
        Parse SSW HTML response and extract tracking information

        Args:
            html_content: Raw HTML from SSW system

        Returns:
            Dictionary with tracking data or None if parsing fails
        """
        if not html_content or len(html_content) < MIN_HTML_LENGTH:
            logger.warning("HTML content too short or empty")
            return None

        try:
            soup = BeautifulSoup(html_content, 'html5lib')
            status_paragraphs = soup.find_all("p", class_="tdb")

            if not status_paragraphs or len(status_paragraphs) < 3:
                logger.warning("Could not find required status paragraphs in HTML")
                return None

            # Extract data from HTML paragraphs
            unidade_text = status_paragraphs[0].get_text(strip=True)
            location_date_text = status_paragraphs[1].get_text(strip=True)
            status_text = status_paragraphs[2].get_text(strip=True)

            # Parse components
            unidade = SSWParser._extract_unidade(unidade_text)
            location = SSWParser._extract_location(location_date_text)
            date_str, time_str = SSWParser._extract_datetime(location_date_text)
            status, status_raw = SSWParser._extract_status(status_text)
            occurred_at = SSWParser._format_datetime(date_str, time_str)

            result = {
                "unidade": unidade,
                "location": location,
                "date": date_str,
                "time": time_str,
                "datetime": occurred_at,
                "status": status,
                "status_raw": status_raw,
                "description": status_raw,
            }

            logger.debug(f"Parsed tracking data: {result}")
            return result

        except Exception as e:
            logger.error(f"Error parsing SSW HTML: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_unidade(text: str) -> Optional[str]:
        """Extract unit code from text"""
        match = re.search(r'(\d{4})', text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_location(text: str) -> Optional[str]:
        """Extract location from text"""
        location_words = re.findall(r'(\w+)', text)
        return " ".join(location_words[:2]) if len(location_words) >= 2 else None

    @staticmethod
    def _extract_datetime(text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract date and time from text"""
        date_match = re.search(r'(\d{2}/\d{2}/\d{2,4})', text)
        time_match = re.search(r'(\d{2}:\d{2})', text)
        
        date_str = date_match.group(1) if date_match else None
        time_str = time_match.group(1) if time_match else None
        
        return date_str, time_str

    @staticmethod
    def _extract_status(text: str) -> tuple[str, str]:
        """Extract status code and raw status from text"""
        status_raw = text.split("  ")[0].strip()
        status = STATUS_MAPPING.get(status_raw, "in_transit")
        return status, status_raw

    @staticmethod
    def _format_datetime(date_str: Optional[str], time_str: Optional[str]) -> Optional[str]:
        """Convert Brazilian date format to ISO format"""
        if not date_str or not time_str:
            return None

        try:
            # Handle both DD/MM/YY and DD/MM/YYYY formats
            if len(date_str) == 8:  # DD/MM/YY
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M")
            else:  # DD/MM/YYYY
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
            return dt.isoformat()
        except ValueError as e:
            logger.warning(f"Could not parse date/time: {e}")
            return None

    @staticmethod
    def is_delivered(tracking_data: Dict[str, Any]) -> bool:
        """
        Check if shipment is delivered
        
        Args:
            tracking_data: Parsed tracking data
            
        Returns:
            True if shipment status is 'delivered'
        """
        return tracking_data.get('status') == 'delivered'

    @staticmethod
    def has_new_update(
        tracking_data: Dict[str, Any],
        last_event: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Check if tracking data represents a new update
        
        Compares status, date, time, and description with last known event.

        Args:
            tracking_data: Newly parsed tracking data
            last_event: Last tracking event from database

        Returns:
            True if this represents a new update
        """
        if not last_event:
            return True

        # Compare key fields
        for field in ['status', 'date', 'time']:
            if tracking_data.get(field) != last_event.get(field):
                return True

        # Compare descriptions (case-insensitive)
        new_desc = tracking_data.get('description', '').lower()
        old_desc = last_event.get('description', '').lower()
        if new_desc != old_desc:
            return True

        return False
